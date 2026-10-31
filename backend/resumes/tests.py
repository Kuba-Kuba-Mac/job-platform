"""Тесты S-01: резюме соискателя."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User

from .models import Resume, Skill

PWD = "Str0ng-Pass-2026"

RESUME = {
    "title": "Junior Python-разработчик",
    "full_name": "Айбек Тестов",
    "city": "Бишкек",
    "contact_email": "aibek@example.kg",
    "salary": 40000,
    "experience": "Стажировка 3 месяца",
    "education": "КГТУ, ПОКС, 2027",
    "languages": ["кыргызский", "русский", "английский B1"],
    "skills": ["Python", " django ", "SQL", "python"],
}


class ResumeTests(APITestCase):
    def setUp(self):
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER)
        self.other = User.objects.create_user("o@x.kg", PWD, role=Role.SEEKER)
        self.employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)

    def test_create_and_normalize_skills(self):
        self.client.force_authenticate(self.seeker)
        resp = self.client.post("/api/resumes/", RESUME, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["skills"], ["django", "python", "sql"])
        self.assertEqual(resp.data["languages"], RESUME["languages"])
        self.assertEqual(Skill.objects.count(), 3)

    def test_update_skills(self):
        self.client.force_authenticate(self.seeker)
        rid = self.client.post("/api/resumes/", RESUME, format="json").data["id"]
        resp = self.client.patch(f"/api/resumes/{rid}/", {"skills": ["Go"], "salary": 50000}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["skills"], ["go"])
        self.assertEqual(resp.data["salary"], 50000)

    def test_patch_without_skills_keeps_them(self):
        self.client.force_authenticate(self.seeker)
        rid = self.client.post("/api/resumes/", RESUME, format="json").data["id"]
        resp = self.client.patch(f"/api/resumes/{rid}/", {"city": "Ош"}, format="json")
        self.assertEqual(len(resp.data["skills"]), 3)

    def test_list_only_own(self):
        Resume.objects.create(seeker=self.other, title="Чужое", full_name="X")
        self.client.force_authenticate(self.seeker)
        self.client.post("/api/resumes/", RESUME, format="json")
        resp = self.client.get("/api/resumes/")
        self.assertEqual(resp.data["count"], 1)

    def test_cannot_edit_foreign(self):
        foreign = Resume.objects.create(seeker=self.other, title="Чужое", full_name="X")
        self.client.force_authenticate(self.seeker)
        resp = self.client.patch(f"/api/resumes/{foreign.id}/", {"title": "Взлом"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_employer_forbidden(self):
        self.client.force_authenticate(self.employer)
        resp = self.client.post("/api/resumes/", RESUME, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_required_fields(self):
        self.client.force_authenticate(self.seeker)
        resp = self.client.post("/api/resumes/", {"city": "Бишкек"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", resp.data)
        self.assertIn("full_name", resp.data)

    def test_negative_salary_rejected(self):
        self.client.force_authenticate(self.seeker)
        resp = self.client.post("/api/resumes/", {**RESUME, "salary": -5}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_skill_suggestions(self):
        Skill.objects.create(name="python")
        Skill.objects.create(name="java")
        resp = self.client.get("/api/skills/?q=PY")
        self.assertEqual([s["name"] for s in resp.data], ["python"])
