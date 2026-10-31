"""Тесты E-01: профиль компании."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User

from .models import Company, ModerationStatus

URL = "/api/companies/me/"
PWD = "Str0ng-Pass-2026"


class MyCompanyTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user("hr@corp.kg", PWD, role=Role.EMPLOYER)
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER)

    def test_seeker_forbidden(self):
        self.client.force_authenticate(self.seeker)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_403_FORBIDDEN)

    def test_create_get_update(self):
        self.client.force_authenticate(self.employer)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_404_NOT_FOUND)

        resp = self.client.post(
            URL,
            {"name": "Код Кыргызстан", "description": "IT-компания", "website": "https://example.kg"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["moderation_status"], "pending")

        # повторное создание запрещено
        self.assertEqual(self.client.post(URL, {"name": "X"}, format="json").status_code, 400)

        company = Company.objects.get(owner=self.employer)
        company.moderation_status = ModerationStatus.APPROVED
        company.save()

        resp = self.client.patch(URL, {"city": "Бишкек"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["city"], "Бишкек")
        # после правки компания снова уходит на модерацию
        self.assertEqual(resp.data["moderation_status"], "pending")

    def test_cannot_set_moderation_status_himself(self):
        self.client.force_authenticate(self.employer)
        resp = self.client.post(URL, {"name": "Хитрая", "moderation_status": "approved"}, format="json")
        self.assertEqual(resp.data["moderation_status"], "pending")

    def test_invalid_website(self):
        self.client.force_authenticate(self.employer)
        resp = self.client.post(URL, {"name": "A", "website": "not-a-url"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class PublicCompanyListTests(APITestCase):
    def test_only_approved_visible(self):
        e1 = User.objects.create_user("a@x.kg", PWD, role=Role.EMPLOYER)
        e2 = User.objects.create_user("b@x.kg", PWD, role=Role.EMPLOYER)
        Company.objects.create(owner=e1, name="Видимая", moderation_status=ModerationStatus.APPROVED)
        Company.objects.create(owner=e2, name="Скрытая")

        resp = self.client.get("/api/companies/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [c["name"] for c in resp.data["results"]]
        self.assertEqual(names, ["Видимая"])
