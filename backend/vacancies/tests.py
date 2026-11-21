"""Тесты E-02: создание, редактирование и архивация вакансий."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from companies.models import Company, ModerationStatus

from .models import Vacancy

PWD = "Str0ng-Pass-2026"
MY = "/api/vacancies/my/"

VACANCY = {
    "title": "Junior Python-разработчик",
    "description": "Пишем backend на Django.",
    "city": "Бишкек",
    "salary_from": 30000,
    "salary_to": 50000,
    "experience": "none",
    "employment_type": "full",
    "schedule": "remote",
    "is_internship": True,
    "skills": ["Python", " django ", "python"],
}


def approved_company(owner, name="Тоо-Код"):
    return Company.objects.create(owner=owner, name=name, moderation_status=ModerationStatus.APPROVED)


class MyVacancyTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user("hr@corp.kg", PWD, role=Role.EMPLOYER)
        self.company = approved_company(self.employer)
        self.client.force_authenticate(self.employer)

    def create(self, **overrides):
        return self.client.post(MY, {**VACANCY, **overrides}, format="json")

    def test_create(self):
        resp = self.create(moderation_status="approved", is_archived=True)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["skills"], ["django", "python"])
        # статус модерации и архив выставить себе нельзя
        self.assertEqual(resp.data["moderation_status"], "pending")
        self.assertFalse(resp.data["is_archived"])
        self.assertEqual(Vacancy.objects.get().company, self.company)

    def test_create_without_company(self):
        other = User.objects.create_user("new@corp.kg", PWD, role=Role.EMPLOYER)
        self.client.force_authenticate(other)
        resp = self.create()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("профиль компании", resp.data["detail"])

    def test_required_fields_and_choices(self):
        resp = self.client.post(MY, {"city": "Ош", "schedule": "night"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ["title", "description", "schedule"]:
            self.assertIn(field, resp.data)

    def test_salary_range(self):
        resp = self.create(salary_from=60000, salary_to=50000)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("salary_to", resp.data)
        self.assertEqual(self.create(salary_from=-1).status_code, status.HTTP_400_BAD_REQUEST)
        # открытый диапазон допустим
        self.assertEqual(self.create(salary_from=None, salary_to=40000).status_code, status.HTTP_201_CREATED)

    def test_patch_salary_checked_against_saved_value(self):
        vid = self.create().data["id"]
        resp = self.client.patch(f"{MY}{vid}/", {"salary_from": 70000}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_returns_to_moderation(self):
        vid = self.create().data["id"]
        Vacancy.objects.filter(pk=vid).update(moderation_status=ModerationStatus.APPROVED)
        resp = self.client.patch(f"{MY}{vid}/", {"title": "Middle Python", "skills": ["Go"]}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["moderation_status"], "pending")
        self.assertEqual(resp.data["skills"], ["go"])

    def test_patch_without_skills_keeps_them(self):
        vid = self.create().data["id"]
        resp = self.client.patch(f"{MY}{vid}/", {"city": "Ош"}, format="json")
        self.assertEqual(resp.data["skills"], ["django", "python"])

    def test_delete_and_put_not_allowed(self):
        vid = self.create().data["id"]
        self.assertEqual(self.client.delete(f"{MY}{vid}/").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.put(f"{MY}{vid}/", VACANCY, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Vacancy.objects.filter(pk=vid).exists())

    def test_archive_and_restore(self):
        active = self.create().data["id"]
        archived = self.create(title="Старая").data["id"]

        resp = self.client.post(f"{MY}{archived}/archive/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["is_archived"])

        ids = lambda q: [v["id"] for v in self.client.get(MY + q).data["results"]]  # noqa: E731
        self.assertEqual(ids("?archived=false"), [active])
        self.assertEqual(ids("?archived=true"), [archived])
        self.assertEqual(sorted(ids("")), sorted([active, archived]))

        resp = self.client.post(f"{MY}{archived}/restore/")
        self.assertFalse(resp.data["is_archived"])
        self.assertEqual(sorted(ids("?archived=false")), sorted([active, archived]))

    def test_foreign_vacancy_404(self):
        other = User.objects.create_user("other@corp.kg", PWD, role=Role.EMPLOYER)
        foreign = Vacancy.objects.create(
            company=approved_company(other, "Чужая"), title="Чужая", description="-", city="Ош"
        )
        url = f"{MY}{foreign.id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(url, {"title": "X"}, format="json").status_code, 404)
        self.assertEqual(self.client.post(f"{url}archive/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(MY).data["count"], 0)
        foreign.refresh_from_db()
        self.assertFalse(foreign.is_archived)

    def test_roles(self):
        seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER)
        self.client.force_authenticate(seeker)
        self.assertEqual(self.client.get(MY).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.create().status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(MY).status_code, status.HTTP_401_UNAUTHORIZED)


class PublicVacancyTests(APITestCase):
    def setUp(self):
        employer = User.objects.create_user("hr@corp.kg", PWD, role=Role.EMPLOYER)
        company = approved_company(employer)
        hidden_employer = User.objects.create_user("hidden@corp.kg", PWD, role=Role.EMPLOYER)
        hidden_company = Company.objects.create(owner=hidden_employer, name="На модерации")

        def make(title, company=company, **kwargs):
            kwargs.setdefault("moderation_status", ModerationStatus.APPROVED)
            return Vacancy.objects.create(company=company, title=title, description="-", city="Бишкек", **kwargs)

        self.published = make("Опубликована")
        make("Ждёт модерации", moderation_status=ModerationStatus.PENDING)
        make("Отклонена", moderation_status=ModerationStatus.REJECTED)
        self.archived = make("В архиве", is_archived=True)
        make("Компания не одобрена", company=hidden_company)

    def test_only_published_visible(self):
        resp = self.client.get("/api/vacancies/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([v["title"] for v in resp.data["results"]], ["Опубликована"])
        self.assertEqual(resp.data["results"][0]["company"]["name"], "Тоо-Код")
        self.assertNotIn("moderation_status", resp.data["results"][0])

    def test_detail(self):
        self.assertEqual(self.client.get(f"/api/vacancies/{self.published.id}/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/vacancies/{self.archived.id}/").status_code, 404)

    def test_read_only(self):
        employer = User.objects.get(email="hr@corp.kg")
        self.client.force_authenticate(employer)
        resp = self.client.post("/api/vacancies/", VACANCY, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
