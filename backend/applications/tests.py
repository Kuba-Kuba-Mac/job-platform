"""Тесты откликов: S-04 (отклик), S-05 (мои отклики), E-03 (отклики на вакансию), E-04 (смена статуса)."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from companies.models import Company, ModerationStatus
from resumes.models import Resume
from vacancies.models import Vacancy

from .models import Application, ApplicationStatus
from .services import application_created

PWD = "Str0ng-Pass-2026"
APPLY = "/api/applications/"


class ApplicationsBase(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user("hr@corp.kg", PWD, role=Role.EMPLOYER)
        self.company = Company.objects.create(
            owner=self.employer, name="Тоо-Код", moderation_status=ModerationStatus.APPROVED
        )
        self.vacancy = self.make_vacancy("Python")
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER, full_name="Айбек")
        self.resume = Resume.objects.create(seeker=self.seeker, title="Junior Python", full_name="Айбек Тестов")
        self.other = User.objects.create_user("o@x.kg", PWD, role=Role.SEEKER)
        self.other_resume = Resume.objects.create(seeker=self.other, title="Чужое", full_name="Другой")

    def make_vacancy(self, title, company=None, **kw):
        kw.setdefault("moderation_status", ModerationStatus.APPROVED)
        return Vacancy.objects.create(
            company=company or self.company, title=title, description="-", city="Бишкек", **kw
        )

    def apply(self, vacancy=None, resume=None, letter="Хочу к вам"):
        self.client.force_authenticate(self.seeker)
        return self.client.post(
            APPLY,
            {
                "vacancy_id": (vacancy or self.vacancy).id,
                "resume_id": (resume or self.resume).id,
                "cover_letter": letter,
            },
            format="json",
        )


class ApplyTests(ApplicationsBase):
    """S-04"""

    def test_apply(self):
        received = []
        application_created.connect(lambda **kw: received.append(kw["application"]), weak=False)
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.apply()
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["status"], "new")
        self.assertEqual(resp.data["resume"]["title"], "Junior Python")
        self.assertEqual(resp.data["cover_letter"], "Хочу к вам")
        self.assertEqual(resp.data["vacancy"]["title"], "Python")
        # сигнал для будущего письма работодателю (N-01)
        self.assertEqual([a.id for a in received], [resp.data["id"]])
        application_created.receivers.clear()

    def test_cannot_apply_twice(self):
        self.apply()
        resp = self.apply(letter="Ещё раз")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vacancy_id", resp.data)
        self.assertEqual(Application.objects.count(), 1)

    def test_cannot_apply_to_unpublished(self):
        cases = [
            self.make_vacancy("Архив", is_archived=True),
            self.make_vacancy("На модерации", moderation_status=ModerationStatus.PENDING),
            self.make_vacancy("Отклонена", moderation_status=ModerationStatus.REJECTED),
        ]
        hidden_owner = User.objects.create_user("h@corp.kg", PWD, role=Role.EMPLOYER)
        hidden_company = Company.objects.create(owner=hidden_owner, name="Скрытая")
        cases.append(self.make_vacancy("Компания не одобрена", company=hidden_company))
        for vacancy in cases:
            resp = self.apply(vacancy)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, vacancy.title)
        self.assertFalse(Application.objects.exists())

    def test_cannot_use_foreign_resume(self):
        resp = self.apply(resume=self.other_resume)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["resume_id"], ["Резюме не найдено."])

    def test_cover_letter_optional_and_limited(self):
        self.assertEqual(self.apply(letter="").status_code, status.HTTP_201_CREATED)
        other_vacancy = self.make_vacancy("Django")
        self.assertEqual(self.apply(other_vacancy, letter="x" * 3001).status_code, status.HTTP_400_BAD_REQUEST)

    def test_vacancy_shows_application_status_to_seeker(self):
        self.apply()
        self.assertEqual(self.client.get(f"/api/vacancies/{self.vacancy.id}/").data["application_status"], "new")
        self.client.force_authenticate(self.other)
        self.assertIsNone(self.client.get(f"/api/vacancies/{self.vacancy.id}/").data["application_status"])

    def test_other_roles(self):
        self.client.force_authenticate(self.employer)
        resp = self.client.post(APPLY, {"vacancy_id": self.vacancy.id, "resume_id": self.resume.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        admin = User.objects.create_user("a@x.kg", PWD, role=Role.ADMIN)
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.post(APPLY, {}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(APPLY, {}, format="json").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deleting_resume_keeps_application(self):
        aid = self.apply().data["id"]
        self.resume.delete()
        self.assertIsNone(Application.objects.get(pk=aid).resume)
        self.assertEqual(Application.objects.get(pk=aid).status, ApplicationStatus.NEW)


class MyApplicationsTests(ApplicationsBase):
    """S-05"""

    def test_list_own_with_statuses(self):
        self.apply()
        second = self.make_vacancy("Django")
        self.apply(second)
        Application.objects.filter(vacancy=second).update(status=ApplicationStatus.INVITED)
        Application.objects.create(vacancy=self.vacancy, seeker=self.other, resume=self.other_resume)

        self.client.force_authenticate(self.seeker)
        data = self.client.get(APPLY).data
        self.assertEqual(data["count"], 2)
        self.assertEqual(
            {a["vacancy"]["title"]: a["status"] for a in data["results"]}, {"Python": "new", "Django": "invited"}
        )
        self.assertEqual(self.client.get(APPLY + "?status=invited").data["count"], 1)
        self.assertEqual(self.client.get(APPLY + "?status=unknown").status_code, status.HTTP_400_BAD_REQUEST)

    def test_archived_vacancy_still_listed(self):
        self.apply()
        Vacancy.objects.filter(pk=self.vacancy.pk).update(is_archived=True)
        self.client.force_authenticate(self.seeker)
        self.assertEqual(self.client.get(APPLY).data["count"], 1)

    def test_foreign_application_not_accessible(self):
        foreign = Application.objects.create(vacancy=self.vacancy, seeker=self.other, resume=self.other_resume)
        self.client.force_authenticate(self.seeker)
        self.assertEqual(self.client.get(f"{APPLY}{foreign.id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_no_update_or_delete_by_seeker(self):
        aid = self.apply().data["id"]
        self.assertEqual(self.client.patch(f"{APPLY}{aid}/", {"status": "invited"}).status_code, 405)
        self.assertEqual(self.client.delete(f"{APPLY}{aid}/").status_code, 405)
        self.assertEqual(Application.objects.get(pk=aid).status, ApplicationStatus.NEW)

    def test_list_query_count(self):
        for i in range(5):
            self.apply(self.make_vacancy(f"V{i}"))
        self.client.force_authenticate(self.seeker)
        with self.assertNumQueries(3):  # count, страница с вакансией/компанией/резюме, навыки
            self.client.get(APPLY)

    def test_other_roles(self):
        self.client.force_authenticate(self.employer)
        self.assertEqual(self.client.get(APPLY).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(APPLY).status_code, status.HTTP_401_UNAUTHORIZED)
