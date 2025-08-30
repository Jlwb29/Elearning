from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from courses.models import Course, Enrollment
from .models import ChatMessage


class CourseChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.course_id = int(self.scope["url_route"]["kwargs"]["course_id"])

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        allowed = await self._user_allowed(self.user.id, self.course_id)
        if not allowed:
            await self.close(code=4003)
            return

        self.group_name = f"course_{self.course_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def receive_json(self, content, **kwargs):
        if content.get("action") == "clear":
            can_clear = await self._user_can_clear(self.user.id, self.course_id)
            if not can_clear:
                return
            await self._clear_messages(self.course_id)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.cleared",
                    "payload": {
                        "event": "chat_cleared",
                        "by": self.user.username,
                        "created_at": now().isoformat(),
                    },
                },
            )
            return

        text = (content.get("message") or "").strip()
        if not text:
            return

        msg = await self._save_message(self.user.id, self.course_id, text)
        payload = {
            "event": "message",
            "id": msg.id,
            "user": self.user.username,
            "text": msg.text,
            "created_at": msg.created_at.isoformat(),
        }
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "payload": payload}
        )

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def chat_cleared(self, event):
        await self.send_json(event["payload"])

    async def notify_enrolled(self, event):
        await self.send_json(event["payload"])

    async def notify_material(self, event):
        await self.send_json(event["payload"])

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def _user_allowed(self, user_id, course_id):
        try:
            c = Course.objects.only("id", "created_by_id").get(pk=course_id)
        except Course.DoesNotExist:
            return False
        if c.created_by_id == user_id:
            return True
        return Enrollment.objects.filter(course_id=course_id, user_id=user_id).exists()

    @database_sync_to_async
    def _user_can_clear(self, user_id, course_id):
        try:
            c = Course.objects.only("id", "created_by_id").get(pk=course_id)
        except Course.DoesNotExist:
            return False
        if c.created_by_id == user_id:
            return True
        return Enrollment.objects.filter(
            course_id=course_id, user_id=user_id, role="TEACHER"
        ).exists()

    @database_sync_to_async
    def _clear_messages(self, course_id):
        ChatMessage.objects.filter(course_id=course_id).delete()

    @database_sync_to_async
    def _save_message(self, user_id, course_id, text):
        return ChatMessage.objects.create(
            user_id=user_id, course_id=course_id, text=text, created_at=now()
        )
