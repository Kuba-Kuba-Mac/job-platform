"""Тесты A-01 (блокировка пользователей) и A-02 (модерация)."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from companies.models import Company, ModerationStatus
from vacancies.models import Vacancy

PWD = "Str0ng-Pass-2026"
USERS = "/api/admin/users/"
MOD_V = "/api/admin/moderation/vacancies/"
MOD_C = "/api/admin/moderation/companies/"


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


class ModerationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin@x.kg", PWD, role=Role.ADMIN)
        self.employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER)
        self.company = Company.objects.create(owner=self.employer, name="Тоо-Код")
        self.vacancy = Vacancy.objects.create(company=self.company, title="Python", description="-", city="Бишкек")
        self.client.force_authenticate(self.admin)

    def public_titles(self):
        self.client.force_authenticate(None)
        titles = [v["title"] for v in self.client.get("/api/vacancies/").data["results"]]
        self.client.force_authenticate(self.admin)
        return titles

    def test_queues_show_pending_oldest_first(self):
        Vacancy.objects.create(
            company=self.company, title="Одобрена", description="-", city="Ош", moderation_status="approved"
        )
        resp = self.client.get(MOD_V)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([v["title"] for v in resp.data["results"]], ["Python"])
        self.assertEqual(resp.data["results"][0]["company"]["moderation_status"], "pending")
        self.assertEqual(self.client.get(MOD_V + "?status=all").data["count"], 2)
        self.assertEqual(self.client.get(MOD_C).data["results"][0]["owner_email"], "e@x.kg")

    def test_vacancy_visible_only_after_vacancy_and_company_approved(self):
        self.client.post(f"{MOD_V}{self.vacancy.id}/approve/")
        self.assertEqual(self.public_titles(), [])  # компания ещё на модерации
        resp = self.client.post(f"{MOD_C}{self.company.id}/approve/")
        self.assertEqual(resp.data["moderation_status"], "approved")
        self.assertEqual(self.public_titles(), ["Python"])

    def test_reject_requires_reason_and_employer_sees_it(self):
        resp = self.client.post(f"{MOD_V}{self.vacancy.id}/reject/", {"reason": "  "})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        resp = self.client.post(f"{MOD_V}{self.vacancy.id}/reject/", {"reason": "Нет описания обязанностей"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["moderation_status"], "rejected")

        self.client.force_authenticate(self.employer)
        mine = self.client.get(f"/api/vacancies/my/{self.vacancy.id}/").data
        self.assertEqual(mine["moderation_status"], "rejected")
        self.assertEqual(mine["rejection_reason"], "Нет описания обязанностей")
        # после правки — снова на модерации, причина стирается
        mine = self.client.patch(f"/api/vacancies/my/{self.vacancy.id}/", {"description": "Обязанности: …"}).data
        self.assertEqual(mine["moderation_status"], "pending")
        self.assertEqual(mine["rejection_reason"], "")

    def test_rejected_company_reason_visible_to_owner(self):
        self.client.post(f"{MOD_C}{self.company.id}/reject/", {"reason": "Укажите сайт"})
        self.client.force_authenticate(self.employer)
        data = self.client.get("/api/companies/me/").data
        self.assertEqual((data["moderation_status"], data["rejection_reason"]), ("rejected", "Укажите сайт"))
        data = self.client.patch("/api/companies/me/", {"website": "https://tookod.kg"}, format="json").data
        self.assertEqual((data["moderation_status"], data["rejection_reason"]), ("pending", ""))

    def test_reapproving_clears_reason(self):
        self.client.post(f"{MOD_V}{self.vacancy.id}/reject/", {"reason": "Опечатка"})
        resp = self.client.post(f"{MOD_V}{self.vacancy.id}/approve/")
        self.assertEqual(resp.data["rejection_reason"], "")

    def test_unknown_object_404(self):
        self.assertEqual(self.client.post(f"{MOD_V}99999/approve/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(f"{MOD_C}99999/approve/").status_code, status.HTTP_404_NOT_FOUND)

    def test_other_roles_forbidden(self):
        for user in (self.employer, self.seeker):
            self.client.force_authenticate(user)
            for url in (MOD_V, MOD_C, f"{MOD_V}{self.vacancy.id}/approve/", f"{MOD_C}{self.company.id}/approve/"):
                method = self.client.post if url.endswith("approve/") else self.client.get
                self.assertEqual(method(url).status_code, status.HTTP_403_FORBIDDEN, (user, url))
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(MOD_V).status_code, status.HTTP_401_UNAUTHORIZED)
        self.vacancy.refresh_from_db()
        self.company.refresh_from_db()
        self.assertEqual(self.vacancy.moderation_status, ModerationStatus.PENDING)
        self.assertEqual(self.company.moderation_status, ModerationStatus.PENDING)
