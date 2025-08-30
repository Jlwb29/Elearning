from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/chat/course/<int:course_id>/", consumers.CourseChatConsumer.as_asgi()),
]
