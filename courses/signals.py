from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Enrollment, CourseMaterial

@receiver(post_save, sender=Enrollment)
def notify_teacher_on_enrollment(sender, instance, created, **kwargs):
    if not created or instance.role != "STUDENT":
        return

    course = instance.course
    student = instance.user
    layer = get_channel_layer()

    async_to_sync(layer.group_send)(
        f"course_{course.id}",
        {
            "type": "notify.enrolled",  
            "payload": 
            {
                "event": "enrolled",
                "user": student.username,
                "course": course.title,     
                "text": f"{student.username} enrolled in {course.title}",
                "created_at": timezone.now().isoformat()
            },
        },
    )

    if course.created_by and course.created_by.email:
        try:
            send_mail(
                subject=f"New enrollment — {course.title}",
                message=f"{student.username} has enrolled in “{course.title}”",
                from_email=None,                       
                recipient_list=[course.created_by.email],
                fail_silently=True             
            )
        except Exception:
            pass


@receiver(post_save, sender=CourseMaterial)
def notify_students_on_material(sender, instance, created, **kwargs):
    if not created:
        return

    course = instance.course

    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"course_{course.id}",
        {
            "type": "notify.material",
            "payload": {
                "event": "material",
                "title": instance.title,
                "course": course.title,
                "created_at": timezone.now().isoformat(),
                "url": instance.url,
                "has_file": bool(instance.file),
            },
        },
    )

    students = (User.objects
                .filter(enrollments__course=course, enrollments__role="STUDENT")
                .exclude(email="")
                .distinct())
    for u in students:
        try:
            send_mail(
                subject=f"New material in {course.title}",
                message=f'"{instance.title}" was added to {course.title}',
                from_email=None,
                recipient_list=[u.email],
                fail_silently=True,
            )
        except Exception:
            pass
