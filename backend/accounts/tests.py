"""Тесты F-01, F-02, F-03, F-06."""

from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from .models import Role, User
from .permissions import IsEmployer, IsSeeker

STRONG_PASSWORD = "Str0ng-Pass-2026"


class SeekerOnlyView(APIView):
    permission_classes = [IsSeeker]

    def get(self, request):
        return Response({"ok": True})


class EmployerOnlyView(APIView):
    permission_classes = [IsEmployer]

    def get(self, request):
        return Response({"ok": True})


urlpatterns = [
    path("seeker-only/", SeekerOnlyView.as_view()),
    path("employer-only/", EmployerOnlyView.as_view()),
]


class RegistrationTests(APITestCase):
    url = "/api/auth/register/"

    def test_register_seeker(self):
        resp = self.client.post(self.url, {"email": "Ann@Example.com", "password": STRONG_PASSWORD, "role": "seeker"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["user"]["role"], "seeker")
        self.assertEqual(resp.data["user"]["email"], "ann@example.com")
        self.assertIn("access", resp.data)

    def test_register_employer(self):
        resp = self.client.post(self.url, {"email": "hr@corp.kg", "password": STRONG_PASSWORD, "role": "employer"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(User.objects.get(email="hr@corp.kg").role, Role.EMPLOYER)

    def test_cannot_register_as_admin(self):
        resp = self.client.post(self.url, {"email": "x@x.kg", "password": STRONG_PASSWORD, "role": "admin"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_rejected(self):
        User.objects.create_user("dup@x.kg", STRONG_PASSWORD)
        resp = self.client.post(self.url, {"email": "DUP@x.kg", "password": STRONG_PASSWORD, "role": "seeker"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        resp = self.client.post(self.url, {"email": "w@x.kg", "password": "123", "role": "seeker"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordHashingTests(APITestCase):
    def test_password_stored_as_argon2_hash(self):
        user = User.objects.create_user("hash@x.kg", STRONG_PASSWORD)
        self.assertNotEqual(user.password, STRONG_PASSWORD)
        self.assertTrue(user.password.startswith("argon2"))
        self.assertTrue(user.check_password(STRONG_PASSWORD))


class LoginLogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("me@x.kg", STRONG_PASSWORD, role=Role.EMPLOYER)

    def login(self):
        return self.client.post("/api/auth/login/", {"email": "me@x.kg", "password": STRONG_PASSWORD})

    def test_login_returns_tokens_and_user(self):
        resp = self.login()
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["user"]["role"], "employer")
        self.assertIn("refresh", resp.data)

    def test_wrong_password(self):
        resp = self.client.post("/api/auth/login/", {"email": "me@x.kg", "password": "wrong"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blocked_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_and_logout(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").data["email"], "me@x.kg")

        resp = self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]})
        self.assertEqual(resp.status_code, status.HTTP_205_RESET_CONTENT)
        # отозванный refresh больше не работает
        resp = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordChangeTests(APITestCase):
    url = "/api/auth/password/change/"
    NEW_PASSWORD = "N3w-Secure-Pass!"

    def setUp(self):
        self.user = User.objects.create_user("pw@x.kg", STRONG_PASSWORD)
        self.tokens = self.client.post("/api/auth/login/", {"email": "pw@x.kg", "password": STRONG_PASSWORD}).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tokens['access']}")

    def change(self, old, new):
        return self.client.post(self.url, {"old_password": old, "new_password": new})

    def login(self, password):
        return self.client.post("/api/auth/login/", {"email": "pw@x.kg", "password": password})

    def test_change_password(self):
        resp = self.change(STRONG_PASSWORD, self.NEW_PASSWORD)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

        self.user.refresh_from_db()
        self.assertTrue(self.user.password.startswith("argon2"))
        self.assertEqual(self.login(STRONG_PASSWORD).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.login(self.NEW_PASSWORD).status_code, status.HTTP_200_OK)

    def test_new_tokens_work_and_old_refresh_revoked(self):
        resp = self.change(STRONG_PASSWORD, self.NEW_PASSWORD)
        # старый refresh отозван
        old = self.client.post("/api/auth/refresh/", {"refresh": self.tokens["refresh"]})
        self.assertEqual(old.status_code, status.HTTP_401_UNAUTHORIZED)
        # новый refresh из ответа работает — текущая сессия не вылетает
        new = self.client.post("/api/auth/refresh/", {"refresh": resp.data["refresh"]})
        self.assertEqual(new.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_200_OK)

    def test_wrong_old_password(self):
        resp = self.change("wrong-password", self.NEW_PASSWORD)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["old_password"], ["Текущий пароль указан неверно."])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(STRONG_PASSWORD))

    def test_weak_new_password(self):
        for weak in ["123", "12345678", "password"]:
            resp = self.change(STRONG_PASSWORD, weak)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, weak)
            self.assertIn("new_password", resp.data)

    def test_same_password_rejected(self):
        resp = self.change(STRONG_PASSWORD, STRONG_PASSWORD)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", resp.data)

    def test_requires_auth(self):
        self.client.credentials()
        resp = self.change(STRONG_PASSWORD, self.NEW_PASSWORD)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(ROOT_URLCONF=__name__)
class RolePermissionTests(APITestCase):
    def test_roles(self):
        seeker = User.objects.create_user("s@x.kg", STRONG_PASSWORD, role=Role.SEEKER)
        employer = User.objects.create_user("e@x.kg", STRONG_PASSWORD, role=Role.EMPLOYER)

        self.assertEqual(self.client.get("/seeker-only/").status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(seeker)
        self.assertEqual(self.client.get("/seeker-only/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/employer-only/").status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(employer)
        self.assertEqual(self.client.get("/employer-only/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/seeker-only/").status_code, status.HTTP_403_FORBIDDEN)
