from django.contrib.auth.decorators import login_required
from django.contrib import messages  
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render, redirect
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from courses.models import Course, Enrollment
from .models import ChatMessage
from django.views.decorators.http import require_POST
from django.utils.timezone import now


@login_required
def course_chat_page(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_teacher = (
        course.created_by_id == request.user.id
        or Enrollment.objects.filter(course=course, user=request.user, role="TEACHER").exists()
    )
    is_student = Enrollment.objects.filter(course=course, user=request.user, role="STUDENT").exists()
    if not (is_teacher or is_student):
        return HttpResponseForbidden()

    chat_qs = course.chat_messages.select_related("user").order_by("-created_at")[:50]
    chat_messages = list(chat_qs)[::-1]  

    return render(
        request,
        "rtchat/course_chat.html",
        {"course": course, "chat_messages": chat_messages, "is_teacher": is_teacher},
    )



@login_required
def clear_course_chat(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_teacher = (course.created_by_id == request.user.id or Enrollment.objects.filter(course=course, user=request.user, role="TEACHER").exists())
    if not is_teacher:
        return HttpResponseForbidden()
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    ChatMessage.objects.filter(course=course).delete()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"course_{course.id}", {"type": "chat.cleared"})
    return redirect("course_chat", pk=pk)

@login_required
@require_POST
def course_chat_clear(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)

    is_owner = (course.created_by_id == request.user.id)
    is_teacher = Enrollment.objects.filter(course_id=course_id, user_id=request.user.id, role="TEACHER").exists()
    if not (is_owner or is_teacher):
        return redirect("course_chat", course_id=course_id)

    ChatMessage.objects.filter(course_id=course_id).delete()

    layer = get_channel_layer()
    if layer is not None:
        async_to_sync(layer.group_send)(
            f"course_{course_id}",
            {
                "type": "chat.cleared",
                "payload": {
                    "event": "chat_cleared",
                    "by": request.user.get_username(),
                    "created_at": now().isoformat(),
                },
            },
        )

    return redirect("course_chat", pk=course_id)
