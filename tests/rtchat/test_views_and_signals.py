from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from courses.models import Course, Enrollment
from rtchat.models import ChatMessage


class DummyLayer:
    def __init__(self):
        self.events = []

    async def group_send(self, group, message):
        self.events.append((group, message))


class ChatViewsAndSignalsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user("teach", password="pw")
        self.student = User.objects.create_user("stud", password="pw")
        self.other = User.objects.create_user("other", password="pw")

        Group.objects.get_or_create(name="Teacher")[0].user_set.add(self.teacher)

        self.course = Course.objects.create(
            title="Algebra 101",
            description="Intro",
            created_by=self.teacher,
            start_date=timezone.now().date(),
        )
        Enrollment.objects.create(user=self.student, course=self.course, role="STUDENT")
        ChatMessage.objects.create(course=self.course, user=self.teacher, text="Welcome!")

    def test_chat_page_access(self):
        url = reverse("course_chat", args=[self.course.id])

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username="other", password="pw")
        self.assertEqual(self.client.get(url).status_code, 403)

        self.client.login(username="stud", password="pw")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertContains(self.client.get(url), "Welcome!")

        self.client.login(username="teach", password="pw")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertContains(self.client.get(url), "Welcome!")

    @patch("rtchat.views.get_channel_layer")  
    def test_clear_chat_broadcasts(self, mock_get_layer):
        dummy = DummyLayer()
        mock_get_layer.return_value = dummy
        self.client.login(username="teach", password="pw")
        url = reverse("course_chat_clear", args=[self.course.id])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ChatMessage.objects.filter(course=self.course).count(), 0)
        self.assertTrue(dummy.events, "No group_send recorded")
        group, payload = dummy.events[-1]
        self.assertEqual(group, f"course_{self.course.id}")
        self.assertEqual(payload.get("type"), "chat.cleared")


@patch("channels.layers.get_channel_layer")
def test_enrollment_signal(self, mock_get_layer):
    dummy = DummyLayer()
    mock_get_layer.return_value = dummy
    import importlib
    import courses.signals as signals
    importlib.reload(signals)

    new_student = User.objects.create_user("stud2", password="pw")
    Enrollment.objects.create(user=new_student, course=self.course, role="STUDENT")

    self.assertTrue(dummy.events, "No group_send recorded by signal")
    group, payload = dummy.events[-1]
    self.assertEqual(group, f"course_{self.course.id}")
    self.assertEqual(payload.get("type"), "notify.enrolled")

