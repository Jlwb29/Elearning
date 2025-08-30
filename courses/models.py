from django.db import models
from django.conf import settings

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="courses_created"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Enrollment", related_name="courses_participating", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    ROLE_CHOICES = (
        ("STUDENT", "Student"),
        ("TEACHER", "Teacher"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STUDENT")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user.username} -> {self.course.title} ({self.role})"

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    due_date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.course.title})"


class CourseFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="feedbacks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_feedbacks")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("course", "user")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} → {self.course.title} ({self.rating})"

class CourseBlock(models.Model):
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="blocks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_blocks")
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="course_blocks_created"
    )

    class Meta:
        unique_together = ("course", "user")
        indexes = [models.Index(fields=["course", "user"])]

    def __str__(self):
        return f"{self.user} blocked from {self.course}"
    
class CourseMaterial(models.Model):
    course = models.ForeignKey("Course", related_name="materials", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="materials/", blank=True, null=True)  
    url = models.URLField(blank=True)                                       
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_id} · {self.title}"