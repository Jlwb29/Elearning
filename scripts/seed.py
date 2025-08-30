from datetime import date, timedelta
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from courses.models import Course, Enrollment, Assignment
from accounts.models import Status

@transaction.atomic
def run():
    teacher_group, _ = Group.objects.get_or_create(name="Teacher")
    student_group, _ = Group.objects.get_or_create(name="Student")
    ct = ContentType.objects.get_for_model(Course)
    add_course_perm = Permission.objects.get(codename="add_course", content_type=ct)
    teacher_group.permissions.add(add_course_perm)

    def mkuser(username, first, last, email, group=None, password="pass1234"):
        u, created = User.objects.get_or_create(
            username=username,
            defaults={"first_name": first, "last_name": last, "email": email},
        )
        if created:
            u.set_password(password)
            u.save()
        if group and not u.groups.filter(pk=group.pk).exists():
            u.groups.add(group)
        return u

    teachers = [
        mkuser("taylor", "Taylor", "Lee", "taylor@example.com", teacher_group),
        mkuser("morgan", "Morgan", "Chan", "morgan@example.com", teacher_group),
        mkuser("riley", "Riley", "Tan", "riley@example.com", teacher_group)
    ]
    students = [
        mkuser("alex", "Alex", "Lim", "alex@example.com", student_group),
        mkuser("sam", "Sam", "Ng", "sam@example.com", student_group),
        mkuser("jo", "Jo", "Goh", "jo@example.com", student_group),
        mkuser("kai", "Kai", "Wong", "kai@example.com", student_group),
        mkuser("nia", "Nia", "Ong", "nia@example.com", student_group),
        mkuser("zen", "Zen", "Chua", "zen@example.com", student_group)
    ]

    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@example.com", "admin1234")

    today = date.today()
    course_specs = [
        ("Algebra 101", teachers[0]),
        ("Biology Basics", teachers[1]),
        ("World History", teachers[2])
    ]
    courses = []
    for i, (title, teacher) in enumerate(course_specs):
        c, created = Course.objects.get_or_create(
            title=title,
            defaults={
                "description": f"Introductory {title}",
                "start_date": today + timedelta(days=7 * i),
                "end_date": today + timedelta(days=60 + 7 * i),
                "capacity": 30,
                "created_by": teacher
            },
        )
        if not c.created_by_id:
            c.created_by = teacher
            c.save()
        courses.append(c)

    for c, t in zip(courses, teachers):
        Enrollment.objects.get_or_create(user=t, course=c, defaults={"role": "TEACHER"})

    for idx, s in enumerate(students):
        Enrollment.objects.get_or_create(
            user=s, course=courses[idx % len(courses)], defaults={"role": "STUDENT"}
        )

    for c in courses:
        for j in range(1, 3 + 1):
            Assignment.objects.get_or_create(
                course=c, title=f"{c.title} Assignment {j}",
                defaults={"due_date": today + timedelta(days=14 * j)}
            )

    for u in teachers + students:
        Status.objects.get_or_create(user=u, text=f"Hello from {u.username}!")

    print("✅ Seed complete.")
    print("Teachers: taylor / morgan / riley  | password: pass1234")
    print("Students: alex / sam / jo / kai / nia / zen  | password: pass1234")
    print("Admin: admin / admin1234")

run()
