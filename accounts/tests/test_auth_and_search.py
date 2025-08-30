from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group

def make_user(username, pwd="pass1234", group=None):
    u = User.objects.create_user(username=username, password=pwd, email=f"{username}@ex.com")
    if group:
        u.groups.add(group)
    return u

class PeopleSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher_group = Group.objects.create(name="Teacher")
        cls.student_group = Group.objects.create(name="Student")
        cls.t1 = make_user("t1", group=cls.teacher_group)
        cls.t2 = make_user("t2", group=cls.teacher_group)
        cls.s1 = make_user("s1", group=cls.student_group)

    def test_anonymous_redirects_to_login(self):
        url = reverse("people_search") + "?q=t"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp["Location"])

    def test_student_forbidden(self):
        self.client.login(username="s1", password="pass1234")
        url = reverse("people_search") + "?q=t"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_teacher_can_search(self):
        self.client.login(username="t1", password="pass1234")
        url = reverse("people_search") + "?q=t"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        teachers = list(resp.context["teachers"])
        students = list(resp.context["students"])
        self.assertTrue(any(u.username == "t1" for u in teachers))
        self.assertTrue(any(u.username == "t2" for u in teachers))
        self.assertTrue(all(u in teachers or u in students for u in teachers + students))
        self.assertEqual(len(teachers), len(set(u.id for u in teachers)))

class AuthFlowTests(TestCase):
    def setUp(self):
        Group.objects.get_or_create(name="Teacher")
        Group.objects.get_or_create(name="Student")
        self.user = User.objects.create_user("alice", password="pass1234")

    def test_login_logout(self):
        resp = self.client.post(reverse("login"), {"username": "alice", "password": "pass1234"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.client.get(reverse("home")).wsgi_request.user.is_authenticated)
        self.client.post(reverse("logout"))
        home2 = self.client.get(reverse("home"))
        self.assertFalse(home2.wsgi_request.user.is_authenticated)


    def test_signup_creates_user_and_assigns_student_group_if_configured(self):
        signup_data = {"username": "bob", "password1": "pass1234AA", "password2": "pass1234AA"}
        resp = self.client.post(reverse("signup"), signup_data)
        self.assertEqual(resp.status_code, 302) 
        bob = User.objects.get(username="bob")
        student_group = Group.objects.get(name="Student")
        self.assertIn(student_group, bob.groups.all())
