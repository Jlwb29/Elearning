from django.urls import path
from .views import (
    CourseListView, CourseCreateView, TeacherCourseListView, CourseDetailView,
    CourseMultiEnrollView, StudentCourseListView,
    leave_feedback, course_roster, course_roster, remove_student, block_student, unblock_student,CourseMaterialCreateView,
    course_home, CourseMaterialCreateView
)

urlpatterns = [
    path("", CourseListView.as_view(), name="course_list"),
    path("create/", CourseCreateView.as_view(), name="course_create"),
    path("teaching/", TeacherCourseListView.as_view(), name="teacher_course_list"),
    path("<int:pk>/", CourseDetailView.as_view(), name="course_detail"),
    path("enroll/", CourseMultiEnrollView.as_view(), name="course_enroll"),
    path("my/", StudentCourseListView.as_view(), name="student_course_list"),
    path("course/<int:pk>/feedback/", leave_feedback, name="course_feedback"),
    path("course/<int:pk>/roster/", course_roster, name="course_roster"),
    path("course/<int:pk>/roster/", course_roster, name="course_roster"),
    path("course/<int:pk>/remove/<int:user_id>/", remove_student, name="course_remove_student"),
    path("course/<int:pk>/block/<int:user_id>/",  block_student,  name="course_block_student"),
    path("course/<int:pk>/unblock/<int:user_id>/", unblock_student, name="course_unblock_student"),
    path("course/<int:pk>/materials/new/", CourseMaterialCreateView.as_view(), name="material_create"),
    path("course/<int:pk>/home/", course_home, name="course_home"),
    path("course/<int:pk>/materials/new/", CourseMaterialCreateView.as_view(), name="material_create")
]


