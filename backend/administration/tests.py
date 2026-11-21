"""Тесты A-01 (блокировка пользователей) и A-02 (модерация)."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User

PWD = "Str0ng-Pass-2026"
USERS = "/api/admin/users/"


def login(client, email, password=PWD):
    return client.post("/api/auth/login/", {"email": email, "password": password})


class AdminUsersTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin@x.kg", PWD, role=Role.ADMIN)
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER, full_name="Айбек")
        self.employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)
        self.client.force_authenticate(self.admin)

    def test_list_and_filters(self):
        resp = self.client.get(USERS)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 3)
        self.assertEqual(self.client.get(USERS + "?role=employer").data["count"], 1)
        self.assertEqual(self.client.get(USERS + "?q=Айбек").data["results"][0]["email"], "s@x.kg")
        self.assertEqual(self.client.get(USERS + "?is_active=false").data["count"], 0)

    def test_block_revokes_sessions_and_login(self):
        # у соискателя есть активная сессия
        tokens = login(self.client, "s@x.kg").data
        resp = self.client.post(f"{USERS}{self.seeker.id}/block/", {"reason": "Спам"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertFalse(resp.data["is_active"])
        self.assertEqual(resp.data["block_reason"], "Спам")
        self.assertIsNotNone(resp.data["blocked_at"])

        self.client.force_authenticate(None)
        # access-токен больше не работает
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials()
        # refresh-токен отозван
        resp = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        # при входе — понятное сообщение
        resp = login(self.client, "s@x.kg")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data["code"], "user_blocked")
        self.assertIn("заблокирован", resp.data["detail"])

    def test_blocked_message_only_with_correct_password(self):
        self.client.post(f"{USERS}{self.seeker.id}/block/")
        self.client.force_authenticate(None)
        resp = login(self.client, "s@x.kg", "wrong-password")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(resp.data.get("code"), "user_blocked")

    def test_unblock(self):
        self.client.post(f"{USERS}{self.seeker.id}/block/")
        resp = self.client.post(f"{USERS}{self.seeker.id}/unblock/")
        self.assertTrue(resp.data["is_active"])
        self.assertEqual(resp.data["block_reason"], "")
        self.client.force_authenticate(None)
        self.assertEqual(login(self.client, "s@x.kg").status_code, status.HTTP_200_OK)

    def test_cannot_block_self_or_admin(self):
        other_admin = User.objects.create_user("a2@x.kg", PWD, role=Role.ADMIN)
        for user in (self.admin, other_admin):
            resp = self.client.post(f"{USERS}{user.id}/block/")
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            user.refresh_from_db()
            self.assertTrue(user.is_active)

    def test_unknown_user_404(self):
        self.assertEqual(self.client.post(f"{USERS}99999/block/").status_code, status.HTTP_404_NOT_FOUND)

    def test_other_roles_forbidden(self):
        for user in (self.seeker, self.employer):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(USERS).status_code, status.HTTP_403_FORBIDDEN)
            resp = self.client.post(f"{USERS}{self.seeker.id}/block/")
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(USERS).status_code, status.HTTP_401_UNAUTHORIZED)
        self.seeker.refresh_from_db()
        self.assertTrue(self.seeker.is_active)
