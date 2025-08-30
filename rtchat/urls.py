from django.urls import path
from .views import course_chat_page, clear_course_chat
from . import views

urlpatterns = [
    path("course/<int:pk>/chat/", course_chat_page, name="course_chat"),
    path("chat/<int:course_id>/clear/", views.course_chat_clear, name="course_chat_clear"),
]
