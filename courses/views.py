# Django
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, FormView, ListView
from .forms import CourseFeedbackForm, CourseForm, CourseMaterialForm, MultiEnrollForm
from .mixins import StudentRequiredMixin
from .models import Course, CourseBlock, CourseFeedback, CourseMaterial, Enrollment

User = get_user_model()

class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name="Teacher").exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

def _teacher_filter(user):
    return Q(created_by=user) | Q(enrollments__user=user, enrollments__role="TEACHER")

class CourseListView(ListView):
    template_name = "courses/course_list.html"
    context_object_name = "courses"
    model = Course
    ordering = ["-created_at"]

class CourseCreateView(TeacherRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "courses/course_form.html"
    success_url = reverse_lazy("course_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TeacherCourseListView(TeacherRequiredMixin, ListView):
    template_name = "courses/teacher_courses.html"
    context_object_name = "courses"

    def get_queryset(self):
        student_enrs = Enrollment.objects.filter(role="STUDENT").select_related("user")
        return (
            Course.objects.filter(_teacher_filter(self.request.user))
            .distinct()
            .prefetch_related(Prefetch("enrollments", queryset=student_enrs, to_attr="student_enrollments"))
            .annotate(student_count=Count("enrollments", filter=Q(enrollments__role="STUDENT"), distinct=True))
            .order_by("title")
        )

class CourseDetailView(TeacherRequiredMixin, DetailView):
    template_name = "courses/course_detail.html"
    context_object_name = "course"
    model = Course

    def get_queryset(self):
        student_enrs = Enrollment.objects.filter(role="STUDENT").select_related("user")
        return (
            Course.objects.filter(_teacher_filter(self.request.user))
            .distinct()
            .prefetch_related(Prefetch("enrollments", queryset=student_enrs, to_attr="student_enrollments"))
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course_detail_extra_context(ctx, self.object, self.request)
        ctx["students"] = [e.user for e in getattr(self.object, "student_enrollments", [])]
        return ctx

class CourseMultiEnrollView(StudentRequiredMixin, FormView):
    template_name = "courses/course_enroll.html"
    form_class = MultiEnrollForm
    success_url = reverse_lazy("student_course_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        selected = form.cleaned_data["courses"]
        created_any = False
        for course in selected:
            if CourseBlock.objects.filter(course=course, user=user).exists():
                messages.warning(self.request, f"You are blocked from enrolling in “{course.title}”")
                continue
            Enrollment.objects.get_or_create(
                user=user, course=course, defaults={"role": "STUDENT"}
            )
            created_any = True
        if created_any:
            messages.success(self.request, "Enrollment updated")
        return super().form_valid(form)

class StudentCourseListView(StudentRequiredMixin, ListView):
    template_name = "courses/student_courses.html"
    context_object_name = "courses"

    def get_queryset(self):
        return (
            Course.objects
            .filter(enrollments__user=self.request.user, enrollments__role="STUDENT")
            .distinct()
            .order_by("title")
        )

@login_required
def leave_feedback(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_enrolled_student = Enrollment.objects.filter(
        course=course, user=request.user, role="STUDENT"
    ).exists()
    if not is_enrolled_student:
        return HttpResponseForbidden("Only enrolled students can leave feedback")

    instance = CourseFeedback.objects.filter(course=course, user=request.user).first()

    if request.method == "POST":
        form = CourseFeedbackForm(request.POST, instance=instance)
        if form.is_valid():
            fb = form.save(commit=False)
            fb.course = course
            fb.user = request.user
            fb.save()
            messages.success(request, "Your feedback was saved")
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("student_course_list")
    else:
        form = CourseFeedbackForm(instance=instance)

    return render(request, "courses/feedback_form.html", {"course": course, "form": form, "editing": instance is not None})

def course_detail_extra_context(context, course, request):
    context["avg_rating"] = course.feedbacks.aggregate(avg=Avg("rating"))["avg"]
    context["feedbacks"] = course.feedbacks.select_related("user")
    if request.user.is_authenticated:
        context["my_feedback"] = course.feedbacks.filter(user=request.user).first()
    return context

@login_required
def course_roster(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_teacher = (
        course.created_by_id == request.user.id
        or Enrollment.objects.filter(course=course, user=request.user, role="TEACHER").exists()
    )
    if not is_teacher:
        return HttpResponseForbidden("Teachers only")

    students = (
        User.objects.filter(enrollments__course=course, enrollments__role="STUDENT")
        .only("id", "username", "first_name", "last_name", "email")
        .order_by("first_name", "last_name", "username")
        .distinct()
    )

    feedbacks = CourseFeedback.objects.filter(course=course).select_related("user").order_by("-updated_at")
    avg_rating = feedbacks.aggregate(avg=Avg("rating"))["avg"]
    my_feedback = feedbacks.filter(user=request.user).first()

    return render(
        request,
        "courses/course_roster.html",
        {"course": course, "students": list(students), "feedbacks": list(feedbacks), "avg_rating": avg_rating, "my_feedback": my_feedback},
    )

def _is_teacher_for(course, user):
    return (
        course.created_by_id == user.id
        or Enrollment.objects.filter(course=course, user=user, role="TEACHER").exists()
    )

@login_required
@require_POST
def remove_student(request, pk, user_id):
    course = get_object_or_404(Course, pk=pk)
    if not _is_teacher_for(course, request.user):
        return HttpResponseForbidden("Teachers only")
    deleted, _ = Enrollment.objects.filter(course=course, user_id=user_id, role="STUDENT").delete()
    messages.success(request, "Student removed from the course" if deleted else "No student enrollment found to remove")
    return redirect("course_roster", pk=pk)

@login_required
@require_POST
def block_student(request, pk, user_id):
    course = get_object_or_404(Course, pk=pk)
    if not _is_teacher_for(course, request.user):
        return HttpResponseForbidden("Teachers only")
    reason = (request.POST.get("reason") or "").strip()
    CourseBlock.objects.get_or_create(course=course, user_id=user_id, defaults={"reason": reason, "created_by": request.user})
    Enrollment.objects.filter(course=course, user_id=user_id, role="STUDENT").delete()
    messages.success(request, "Student blocked and removed")
    return redirect("course_roster", pk=pk)

@login_required
@require_POST
def unblock_student(request, pk, user_id):
    course = get_object_or_404(Course, pk=pk)
    if not _is_teacher_for(course, request.user):
        return HttpResponseForbidden("Teachers only")
    CourseBlock.objects.filter(course=course, user_id=user_id).delete()
    messages.success(request, "Student unblocked")
    return redirect("course_roster", pk=pk)



class CourseMaterialCreateView(TeacherRequiredMixin, CreateView):
    model = CourseMaterial
    form_class = CourseMaterialForm
    template_name = "courses/material_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=kwargs["pk"])
        if not (self.course.created_by_id == request.user.id or
                Enrollment.objects.filter(course=self.course, user=request.user, role="TEACHER").exists()):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("course_detail", kwargs={"pk": self.course.pk})



def _is_teacher_for(course, user):
    return (course.created_by_id == user.id
            or Enrollment.objects.filter(course=course, user=user, role="TEACHER").exists())

@login_required
def course_home(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_teacher = _is_teacher_for(course, request.user)
    is_student = Enrollment.objects.filter(course=course, user=request.user, role="STUDENT").exists()
    if not (is_teacher or is_student):
        return HttpResponseForbidden()

    materials = course.materials.select_related("created_by").order_by("-created_at")
    return render(request, "courses/course_home.html", {
        "course": course,
        "materials": materials,
        "is_teacher": is_teacher,
    })

class CourseMaterialCreateView(CreateView):
    model = CourseMaterial
    form_class = CourseMaterialForm
    template_name = "courses/material_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=kwargs["pk"])
        if not request.user.is_authenticated or not _is_teacher_for(self.course, request.user):
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("course_home", kwargs={"pk": self.course.pk})
