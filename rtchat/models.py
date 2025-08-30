from django.db import models
from django.conf import settings
from courses.models import Course

class ChatMessage(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chat_messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        preview = (self.text[:40] + "…") if len(self.text) > 40 else self.text
        return f"{self.user.username}: {preview} @ {self.created_at:%Y-%m-%d %H:%M}"
