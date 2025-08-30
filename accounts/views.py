from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import StatusForm
from .models import Status
from courses.models import Course, Enrollment, Assignment


def is_teacher(user):
    return user.is_authenticated and user.groups.filter(name="Teacher").exists()


@login_required
def me_redirect(request):
    return redirect("user_home", username=request.user.username)


@login_required
def user_home(request, username):
    profile_user = get_object_or_404(User, username=username)

    teaches = (
        Course.objects.filter(
            Q(created_by=profile_user) |
            Q(enrollments__user=profile_user, enrollments__role="TEACHER")
        )
        .distinct()
        .order_by("title")
    )

    registered = (
        Course.objects.filter(
            enrollments__user=profile_user, enrollments__role="STUDENT"
        )
        .distinct()
        .order_by("title")
    )

    today = date.today()
    soon = today + timedelta(days=30)
    upcoming = (
        Assignment.objects.filter(
            Q(course__in=teaches) | Q(course__in=registered),
            due_date__gte=today,
            due_date__lte=soon,
        )
        .select_related("course")
        .order_by("due_date")[:10]
    )

    statuses = (
        Status.objects.filter(user=profile_user)
        .only("id", "text", "created_at")
        .order_by("-created_at")
    )

    form = None
    if request.user == profile_user:
        if request.method == "POST":
            form = StatusForm(request.POST)
            if form.is_valid():
                s = form.save(commit=False)
                s.user = request.user
                s.save()
                return redirect("user_home", username=username)
        else:
            form = StatusForm()

    return render(
        request,
        "accounts/user_home.html",
        {
            "profile_user": profile_user,
            "teaches": teaches,
            "registered": registered,
            "upcoming": upcoming,
            "statuses": statuses,
            "form": form,
        },
    )


@login_required
def people_search(request):
    if not is_teacher(request.user):
        return HttpResponseForbidden()

    q = request.GET.get("q", "").strip()
    teachers = students = []
    if q:
        name_q = (
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(username__icontains=q)
            | Q(email__icontains=q)
        )
        teachers = (
            User.objects.filter(name_q, groups__name="Teacher")
            .order_by("first_name", "last_name", "username")
            .distinct()
        )
        students = (
            User.objects.filter(name_q, groups__name="Student")
            .order_by("first_name", "last_name", "username")
            .distinct()
        )

    return render(request, "people_search.html", {
        "query": q,
        "students": students,
        "teachers": teachers,
    })


class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        resp = super().form_valid(form)
        student_group, _ = Group.objects.get_or_create(name="Student")
        self.object.groups.add(student_group)
        return resp
