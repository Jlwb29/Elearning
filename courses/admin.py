from django.contrib import admin
from .models import Course, Enrollment, Assignment

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "start_date", "end_date", "created_at")
    search_fields = ("title", "description")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "role", "created_at")
    list_filter = ("role")

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "due_date")
    list_filter = ("due_date", "course")
