"""Тесты F-01, F-02, F-03, F-04, F-06."""

import re
from io import StringIO
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from applications.models import Application, ApplicationStatus
from companies.models import Company
from favorites.models import Favorite
from profiles.models import Project, SeekerProfile
from resumes.models import Resume
from vacancies.models import Vacancy

from .management.commands.seed_demo import DEMO_PASSWORD
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


def link_params(message, path):
    """Достаёт uid и token из ссылки в письме и проверяет, что ссылка ведёт на нужную страницу frontend."""
    url = re.search(r"https?://\S+", message.body).group(0)
    parsed = urlparse(url)
    assert parsed.path == path, url
    query = parse_qs(parsed.query)
    return {"uid": query["uid"][0], "token": query["token"][0]}


@override_settings(FRONTEND_URL="http://front.test")
class EmailVerificationTests(APITestCase):
    def register(self, email="new@x.kg"):
        return self.client.post(
            "/api/auth/register/",
            # email_verified в запросе игнорируется — подтвердить можно только по ссылке
            {"email": email, "password": STRONG_PASSWORD, "role": "seeker", "email_verified": True},
        )

    def test_register_sends_verification_email(self):
        resp = self.register()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertFalse(resp.data["user"]["email_verified"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["new@x.kg"])
        self.assertIn("http://front.test/verify-email?", mail.outbox[0].body)

    def test_login_allowed_without_verification(self):
        self.register()
        resp = self.client.post("/api/auth/login/", {"email": "new@x.kg", "password": STRONG_PASSWORD})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["user"]["email_verified"])

    def test_verify_and_link_is_single_use(self):
        self.register()
        params = link_params(mail.outbox[0], "/verify-email")

        resp = self.client.post("/api/auth/verify-email/", params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertTrue(User.objects.get(email="new@x.kg").email_verified)

        resp = self.client.post("/api/auth/verify-email/", params)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", resp.data)

    def test_invalid_token_and_uid(self):
        self.register()
        params = link_params(mail.outbox[0], "/verify-email")
        for bad in [{**params, "token": "abc-123"}, {**params, "uid": "!!!"}, {**params, "uid": "OTk5OQ"}]:
            resp = self.client.post("/api/auth/verify-email/", bad)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, bad)
        self.assertFalse(User.objects.get(email="new@x.kg").email_verified)

    def test_token_of_other_user_rejected(self):
        self.register("a@x.kg")
        self.register("b@x.kg")
        a = link_params(mail.outbox[0], "/verify-email")
        b = link_params(mail.outbox[1], "/verify-email")
        resp = self.client.post("/api/auth/verify-email/", {"uid": a["uid"], "token": b["token"]})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend(self):
        user = User.objects.create_user("r@x.kg", STRONG_PASSWORD)
        self.assertEqual(self.client.post("/api/auth/verify-email/resend/").status_code, 401)

        self.client.force_authenticate(user)
        resp = self.client.post("/api/auth/verify-email/resend/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(len(mail.outbox), 1)

        self.client.post("/api/auth/verify-email/", link_params(mail.outbox[0], "/verify-email"))
        user.refresh_from_db()
        self.client.force_authenticate(user)
        resp = self.client.post("/api/auth/verify-email/resend/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 1)

    def test_mail_failure_does_not_break_registration(self):
        with mock.patch("accounts.emails.send_mail", side_effect=OSError("SMTP down")):
            with self.assertLogs("accounts.emails", level="ERROR"):
                resp = self.register()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@x.kg").exists())


@override_settings(FRONTEND_URL="http://front.test")
class PasswordResetTests(APITestCase):
    NEW_PASSWORD = "Fresh-Pass-2027"

    def setUp(self):
        self.user = User.objects.create_user("reset@x.kg", STRONG_PASSWORD)

    def request_reset(self, email):
        return self.client.post("/api/auth/password/reset/", {"email": email})

    def confirm(self, params, password=None):
        return self.client.post(
            "/api/auth/password/reset/confirm/", {**params, "new_password": password or self.NEW_PASSWORD}
        )

    def login(self, password):
        return self.client.post("/api/auth/login/", {"email": "reset@x.kg", "password": password})

    def test_same_response_for_unknown_email(self):
        known = self.request_reset("RESET@x.kg")
        unknown = self.request_reset("nobody@x.kg")
        self.assertEqual(known.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.status_code, known.status_code)
        self.assertEqual(unknown.data, known.data)
        # письмо ушло только существующему пользователю
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reset@x.kg"])
        self.assertIn("http://front.test/reset-password?", mail.outbox[0].body)

    def test_blocked_user_gets_no_email(self):
        self.user.is_active = False
        self.user.save()
        resp = self.request_reset("reset@x.kg")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_revokes_tokens_and_link_is_single_use(self):
        old_refresh = self.login(STRONG_PASSWORD).data["refresh"]
        self.request_reset("reset@x.kg")
        params = link_params(mail.outbox[0], "/reset-password")

        resp = self.confirm(params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(self.login(STRONG_PASSWORD).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.login(self.NEW_PASSWORD).status_code, status.HTTP_200_OK)
        # старые сессии завершены
        resp = self.client.post("/api/auth/refresh/", {"refresh": old_refresh})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        # повторно ссылкой воспользоваться нельзя
        resp = self.confirm(params, "Another-Pass-2028")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        self.request_reset("reset@x.kg")
        params = link_params(mail.outbox[0], "/reset-password")
        resp = self.confirm(params, "12345678")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", resp.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(STRONG_PASSWORD))

    def test_invalid_token(self):
        self.request_reset("reset@x.kg")
        params = link_params(mail.outbox[0], "/reset-password")
        resp = self.confirm({**params, "token": "bad-token"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verification_token_cannot_reset_password(self):
        self.client.force_authenticate(self.user)
        self.client.post("/api/auth/verify-email/resend/")
        self.client.force_authenticate(None)
        params = link_params(mail.outbox[0], "/verify-email")
        self.assertEqual(self.confirm(params).status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(FRONTEND_URL="http://front.test")
class MyProfileTests(APITestCase):
    url = "/api/auth/me/"

    def setUp(self):
        self.user = User.objects.create_user("me@x.kg", STRONG_PASSWORD, email_verified=True)
        self.client.force_authenticate(self.user)

    def patch(self, data):
        return self.client.patch(self.url, data, format="json")

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.patch({"full_name": "X"}).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        resp = self.patch({"full_name": "Айгуль Тестова", "phone": "+996 555 123 456", "city": "Ош"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["full_name"], "Айгуль Тестова")
        self.user.refresh_from_db()
        self.assertEqual(self.user.city, "Ош")
        # email не менялся — повторное подтверждение не нужно
        self.assertTrue(self.user.email_verified)
        self.assertEqual(len(mail.outbox), 0)

    def test_put_not_allowed(self):
        resp = self.client.put(self.url, {"email": "me@x.kg"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_change_role_or_verification(self):
        self.user.email_verified = False
        self.user.save()
        resp = self.patch({"role": "admin", "email_verified": True, "full_name": "Хитрый"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, Role.SEEKER)
        self.assertFalse(self.user.email_verified)
        self.assertEqual(self.user.full_name, "Хитрый")

    def test_change_email_requires_new_verification(self):
        resp = self.patch({"email": "New@X.kg"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["email"], "new@x.kg")
        self.assertFalse(resp.data["email_verified"])
        self.assertEqual(mail.outbox[0].to, ["new@x.kg"])

        resp = self.client.post("/api/auth/verify-email/", link_params(mail.outbox[0], "/verify-email"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_old_verification_link_invalid_after_email_change(self):
        self.user.email_verified = False
        self.user.save()
        self.client.post("/api/auth/verify-email/resend/")
        old_link = link_params(mail.outbox[0], "/verify-email")
        self.patch({"email": "other@x.kg"})
        resp = self.client.post("/api/auth/verify-email/", old_link)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_taken_case_insensitive(self):
        User.objects.create_user("taken@x.kg", STRONG_PASSWORD)
        resp = self.patch({"email": "TAKEN@x.kg"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resp.data)

    def test_same_email_in_other_case_keeps_verification(self):
        resp = self.patch({"email": "ME@X.KG"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertTrue(resp.data["email_verified"])
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_phone(self):
        resp = self.patch({"phone": "позвоните мне"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", resp.data)

    def test_login_returns_profile_fields(self):
        self.user.full_name = "Бакыт"
        self.user.save()
        resp = self.client.post("/api/auth/login/", {"email": "me@x.kg", "password": STRONG_PASSWORD})
        for field in ["email_verified", "full_name", "phone", "city"]:
            self.assertIn(field, resp.data["user"])
        self.assertEqual(resp.data["user"]["full_name"], "Бакыт")


class SeedDemoTests(APITestCase):
    def seed(self, *args):
        call_command("seed_demo", *args, stdout=StringIO())

    def counts(self):
        return {
            "users": User.objects.count(),
            "companies": Company.objects.count(),
            "vacancies": Vacancy.objects.count(),
            "resumes": Resume.objects.count(),
            "projects": Project.objects.count(),
            "applications": Application.objects.count(),
            "favorites": Favorite.objects.count(),
        }

    def test_seed_is_idempotent(self):
        self.seed()
        first = self.counts()
        self.seed()
        self.assertEqual(self.counts(), first)

        self.assertGreaterEqual(Vacancy.objects.published().count(), 10)
        self.assertEqual(Vacancy.objects.filter(moderation_status="pending").count(), 1)
        self.assertEqual(Vacancy.objects.filter(moderation_status="rejected").exclude(rejection_reason="").count(), 1)
        self.assertEqual(Vacancy.objects.filter(is_archived=True).count(), 1)
        self.assertEqual(Company.objects.filter(moderation_status="pending").count(), 1)
        self.assertEqual(SeekerProfile.objects.count(), 3)
        self.assertEqual(set(Application.objects.values_list("status", flat=True)), set(ApplicationStatus.values))
        self.assertGreater(Favorite.objects.count(), 0)
        self.assertEqual(
            list(User.objects.filter(is_active=False).values_list("email", flat=True)), ["seeker4@demo.kg"]
        )
        self.assertTrue(all(u.email.endswith("@demo.kg") and u.email_verified for u in User.objects.all()))

    def test_demo_accounts_can_login(self):
        self.seed()
        for email, role in [("admin@demo.kg", "admin"), ("employer@demo.kg", "employer"), ("seeker@demo.kg", "seeker")]:
            resp = self.client.post("/api/auth/login/", {"email": email, "password": DEMO_PASSWORD})
            self.assertEqual(resp.status_code, status.HTTP_200_OK, email)
            self.assertEqual(resp.data["user"]["role"], role)
        resp = self.client.post("/api/auth/login/", {"email": "seeker4@demo.kg", "password": DEMO_PASSWORD})
        self.assertEqual(resp.data["code"], "user_blocked")

    def test_reset_removes_only_demo_data(self):
        real = User.objects.create_user("real@x.kg", STRONG_PASSWORD)
        self.seed()
        demo_vacancy = Vacancy.objects.first()
        self.seed("--reset")
        self.assertTrue(User.objects.filter(pk=real.pk).exists())
        self.assertFalse(Vacancy.objects.filter(pk=demo_vacancy.pk).exists())
        self.assertGreaterEqual(Vacancy.objects.published().count(), 10)


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
