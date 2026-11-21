"""Тесты S-06: избранные вакансии."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from companies.models import Company, ModerationStatus
from vacancies.models import Vacancy

from .models import Favorite

PWD = "Str0ng-Pass-2026"
URL = "/api/favorites/"


class FavoriteTests(APITestCase):
    def setUp(self):
        employer = User.objects.create_user("hr@corp.kg", PWD, role=Role.EMPLOYER)
        company = Company.objects.create(owner=employer, name="Тоо-Код", moderation_status=ModerationStatus.APPROVED)
        self.employer = employer
        self.vacancy = Vacancy.objects.create(
            company=company, title="Python", description="-", city="Бишкек", moderation_status="approved"
        )
        self.hidden = Vacancy.objects.create(company=company, title="На модерации", description="-", city="Бишкек")
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER)
        self.other = User.objects.create_user("o@x.kg", PWD, role=Role.SEEKER)
        self.client.force_authenticate(self.seeker)

    def add(self, vacancy):
        return self.client.post(URL, {"vacancy_id": vacancy.id}, format="json")

    def test_add_list_remove(self):
        resp = self.add(self.vacancy)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        fid = resp.data["id"]
        data = self.client.get(URL).data
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["vacancy"]["title"], "Python")
        self.assertTrue(data["results"][0]["is_available"])
        self.assertEqual(self.client.delete(f"{URL}{fid}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Favorite.objects.exists())

    def test_cannot_add_twice(self):
        self.add(self.vacancy)
        resp = self.add(self.vacancy)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vacancy_id", resp.data)
        self.assertEqual(Favorite.objects.count(), 1)

    def test_cannot_add_unpublished_or_missing(self):
        self.assertEqual(self.add(self.hidden).status_code, status.HTTP_400_BAD_REQUEST)
        resp = self.client.post(URL, {"vacancy_id": 99999}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unpublished_later_stays_but_marked(self):
        self.add(self.vacancy)
        Vacancy.objects.filter(pk=self.vacancy.pk).update(is_archived=True)
        item = self.client.get(URL).data["results"][0]
        self.assertFalse(item["is_available"])

    def test_foreign_favorite_not_accessible(self):
        foreign = Favorite.objects.create(user=self.other, vacancy=self.vacancy)
        self.assertEqual(self.client.get(URL).data["count"], 0)
        self.assertEqual(self.client.delete(f"{URL}{foreign.id}/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favorite.objects.filter(pk=foreign.pk).exists())

    def test_other_roles(self):
        self.client.force_authenticate(self.employer)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.add(self.vacancy).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_favorite_id_in_search_and_vacancy_page(self):
        fid = self.add(self.vacancy).data["id"]
        self.assertEqual(self.client.get("/api/vacancies/").data["results"][0]["favorite_id"], fid)
        self.assertEqual(self.client.get(f"/api/vacancies/{self.vacancy.id}/").data["favorite_id"], fid)
        # чужое избранное не видно
        self.client.force_authenticate(self.other)
        self.assertIsNone(self.client.get("/api/vacancies/").data["results"][0]["favorite_id"])
        self.client.force_authenticate(None)
        self.assertIsNone(self.client.get("/api/vacancies/").data["results"][0]["favorite_id"])

    def test_search_query_count_for_seeker(self):
        self.add(self.vacancy)
        with self.assertNumQueries(3):
            self.client.get("/api/vacancies/")
