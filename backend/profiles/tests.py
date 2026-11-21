"""Тесты S-08: профиль студента — проекты, GitHub, портфолио."""

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Role, User
from resumes.models import Resume, Skill

from .models import Project, SeekerProfile

PWD = "Str0ng-Pass-2026"
ME = "/api/profiles/me/"
PROJECTS = "/api/profiles/me/projects/"


class MyProfileTests(APITestCase):
    def setUp(self):
        self.seeker = User.objects.create_user(
            "s@x.kg", PWD, role=Role.SEEKER, full_name="Айбек Тестов", city="Бишкек", phone="+996 555 000 111"
        )
        self.client.force_authenticate(self.seeker)

    def test_profile_created_on_first_access(self):
        self.assertFalse(SeekerProfile.objects.exists())
        resp = self.client.get(ME)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user_id"], self.seeker.id)
        self.assertEqual(resp.data["full_name"], "Айбек Тестов")
        self.assertEqual(resp.data["city"], "Бишкек")
        self.assertEqual(resp.data["projects"], [])
        self.assertEqual(SeekerProfile.objects.count(), 1)
        self.client.get(ME)
        self.assertEqual(SeekerProfile.objects.count(), 1)

    def test_update_links(self):
        resp = self.client.patch(
            ME,
            {"about": "Студент КГТУ", "github_url": "https://github.com/aibek", "portfolio_url": "https://aibek.dev"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["github_url"], "https://github.com/aibek")

    def test_github_url_must_point_to_github(self):
        for bad in ["https://gitlab.com/aibek", "https://github.com.evil.kg/aibek", "https://notgithub.com/a"]:
            resp = self.client.patch(ME, {"github_url": bad}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, bad)
            self.assertIn("github_url", resp.data)
        resp = self.client.patch(ME, {"github_url": ""}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_cannot_change_name_through_profile(self):
        self.client.patch(ME, {"full_name": "Другое", "user_id": 999}, format="json")
        self.seeker.refresh_from_db()
        self.assertEqual(self.seeker.full_name, "Айбек Тестов")
        self.assertEqual(self.client.get(ME).data["user_id"], self.seeker.id)

    def test_put_not_allowed(self):
        self.assertEqual(self.client.put(ME, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_skills_merged_from_resumes(self):
        r1 = Resume.objects.create(seeker=self.seeker, title="Python", full_name="А")
        r2 = Resume.objects.create(seeker=self.seeker, title="Data", full_name="А")
        r1.skills.set(Skill.from_names(["Python", "Django"]))
        r2.skills.set(Skill.from_names(["python", "SQL"]))
        other = User.objects.create_user("o@x.kg", PWD, role=Role.SEEKER)
        Resume.objects.create(seeker=other, title="Go", full_name="Б").skills.set(Skill.from_names(["Go"]))

        self.assertEqual(self.client.get(ME).data["skills"], ["django", "python", "sql"])

    def test_roles(self):
        employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)
        self.client.force_authenticate(employer)
        self.assertEqual(self.client.get(ME).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(PROJECTS).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(ME).status_code, status.HTTP_401_UNAUTHORIZED)


class MyProjectsTests(APITestCase):
    def setUp(self):
        self.seeker = User.objects.create_user("s@x.kg", PWD, role=Role.SEEKER)
        self.client.force_authenticate(self.seeker)

    def test_crud(self):
        resp = self.client.post(
            PROJECTS,
            {"title": "Бот расписания", "url": "https://github.com/a/bot", "technologies": "Python, aiogram"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        pid = resp.data["id"]

        resp = self.client.patch(f"{PROJECTS}{pid}/", {"description": "Telegram-бот"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(ME).data["projects"][0]["description"], "Telegram-бот")

        self.assertEqual(self.client.delete(f"{PROJECTS}{pid}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.exists())

    def test_validation(self):
        resp = self.client.post(PROJECTS, {"url": "not-a-url"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", resp.data)
        self.assertIn("url", resp.data)

    def test_foreign_project_404(self):
        other = User.objects.create_user("o@x.kg", PWD, role=Role.SEEKER)
        foreign = Project.objects.create(profile=SeekerProfile.objects.create(user=other), title="Чужой")
        url = f"{PROJECTS}{foreign.id}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.patch(url, {"title": "X"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(PROJECTS).data["count"], 0)
        self.assertTrue(Project.objects.filter(pk=foreign.id, title="Чужой").exists())

    def test_limit(self):
        profile = SeekerProfile.objects.create(user=self.seeker)
        Project.objects.bulk_create(
            [Project(profile=profile, title=f"П{i}") for i in range(Project.MAX_PER_PROFILE)]
        )
        resp = self.client.post(PROJECTS, {"title": "Лишний"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(profile.projects.count(), Project.MAX_PER_PROFILE)


class SeekerProfileVisibilityTests(APITestCase):
    def setUp(self):
        self.seeker = User.objects.create_user(
            "s@x.kg", PWD, role=Role.SEEKER, full_name="Айбек", phone="+996 555 000 111"
        )
        profile = SeekerProfile.objects.create(user=self.seeker, github_url="https://github.com/aibek")
        Project.objects.create(profile=profile, title="Бот")
        self.url = f"/api/profiles/{self.seeker.id}/"

    def test_employer_sees_profile_without_contacts(self):
        employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)
        self.client.force_authenticate(employer)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["full_name"], "Айбек")
        self.assertEqual(len(resp.data["projects"]), 1)
        self.assertNotIn("email", resp.data)
        self.assertNotIn("phone", resp.data)
        self.assertNotIn("s@x.kg", str(resp.data))

    def test_admin_and_owner_see_profile(self):
        admin = User.objects.create_user("a@x.kg", PWD, role=Role.ADMIN)
        for user in (admin, self.seeker):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK, user)

    def test_other_seeker_forbidden(self):
        other = User.objects.create_user("o@x.kg", PWD, role=Role.SEEKER)
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_guest_unauthorized(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_a_seeker_or_blocked_404(self):
        employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)
        self.client.force_authenticate(employer)
        self.assertEqual(self.client.get(f"/api/profiles/{employer.id}/").status_code, status.HTTP_404_NOT_FOUND)
        self.seeker.is_active = False
        self.seeker.save()
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_404_NOT_FOUND)

    def test_read_only(self):
        employer = User.objects.create_user("e@x.kg", PWD, role=Role.EMPLOYER)
        self.client.force_authenticate(employer)
        resp = self.client.patch(self.url, {"about": "взлом"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
