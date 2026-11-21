"""S-02: замер скорости поиска вакансий (нефункциональное требование ТЗ: < 2 с при 1000 вакансий).

Создаёт N вымышленных опубликованных вакансий, прогоняет типичные запросы поиска через настоящий
view (с сериализацией и пагинацией) и печатает время и число SQL-запросов.
По умолчанию все созданные данные откатываются; --keep оставляет их в базе.
"""

import random
import statistics
import time

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIRequestFactory

from accounts.models import Role, User
from companies.models import Company, ModerationStatus
from resumes.models import Skill

from ...models import EmploymentType, Experience, Schedule, Vacancy
from ...views import VacancyViewSet

CITIES = ["Бишкек", "Ош", "Каракол", "Нарын", "Джалал-Абад", "Талас", "Баткен", "Токмок"]
TITLES = ["Python-разработчик", "Frontend-разработчик", "Аналитик данных", "QA-инженер", "Дизайнер", "Менеджер"]
SKILLS = ["python", "django", "react", "sql", "figma", "excel", "docker", "javascript", "git", "linux"]

QUERIES = {
    "без фильтров": "",
    "город": "city=Бишкек",
    "зарплата от 50 000": "salary=50000",
    "опыт + занятость + график": "experience=none,1-3&employment_type=full&schedule=remote,flexible",
    "только стажировки": "internship=true",
    "текст": "q=python",
    "всё сразу, по зарплате": (
        "q=разработчик&city=Бишкек&salary=30000&experience=none,1-3&internship=true&ordering=salary"
    ),
    "страница 10": "page=10",
}


class Rollback(Exception):
    pass


class Command(BaseCommand):
    help = "Замер скорости поиска вакансий на N вымышленных вакансиях (по умолчанию 1000)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1000)
        parser.add_argument("--runs", type=int, default=5, help="Повторов каждого запроса")
        parser.add_argument("--keep", action="store_true", help="Не удалять созданные вакансии")

    def handle(self, *args, count, runs, keep, **options):
        try:
            with transaction.atomic():
                self.generate(count)
                self.measure(runs)
                if not keep:
                    raise Rollback
        except Rollback:
            self.stdout.write("Тестовые вакансии удалены (откат транзакции).")

    def generate(self, count):
        rnd = random.Random(42)
        owners = [User.objects.create_user(f"bench{i}@bench.demo.kg", None, role=Role.EMPLOYER) for i in range(10)]
        companies = [
            Company.objects.create(owner=o, name=f"Бенч-компания {i}", moderation_status=ModerationStatus.APPROVED)
            for i, o in enumerate(owners)
        ]
        vacancies = []
        for i in range(count):
            salary_from = rnd.choice([None, 10000, 20000, 30000, 45000, 60000, 90000])
            salary_to = rnd.choice([None, (salary_from or 20000) + rnd.choice([10000, 30000, 50000])])
            vacancies.append(
                Vacancy(
                    company=rnd.choice(companies),
                    title=f"{rnd.choice(TITLES)} #{i}",
                    description="Вымышленная вакансия для замера скорости поиска. " * 5,
                    city=rnd.choice(CITIES),
                    salary_from=salary_from,
                    salary_to=salary_to,
                    experience=rnd.choice(Experience.values),
                    employment_type=rnd.choice(EmploymentType.values),
                    schedule=rnd.choice(Schedule.values),
                    is_internship=rnd.random() < 0.3,
                    moderation_status=ModerationStatus.APPROVED,
                )
            )
        vacancies = Vacancy.objects.bulk_create(vacancies)
        skills = Skill.from_names(SKILLS)
        Through = Vacancy.skills.through
        Through.objects.bulk_create(
            [Through(vacancy_id=v.id, skill_id=s.id) for v in vacancies for s in rnd.sample(skills, 3)]
        )
        total = Vacancy.objects.published().count()
        self.stdout.write(f"Опубликованных вакансий в базе: {total} (БД: {connection.vendor})")

    def measure(self, runs):
        factory = APIRequestFactory()
        view = VacancyViewSet.as_view({"get": "list"})
        worst = 0.0
        self.stdout.write(f"{'запрос':<28}{'найдено':>9}{'медиана, мс':>13}{'макс, мс':>10}{'SQL':>5}")
        for name, query in QUERIES.items():
            timings = []
            for _ in range(runs):
                request = factory.get(f"/api/vacancies/?{query}", HTTP_HOST="localhost")
                with CaptureQueriesContext(connection) as ctx:
                    start = time.perf_counter()
                    response = view(request)
                    response.render()
                    timings.append((time.perf_counter() - start) * 1000)
            found = response.data["count"] if response.status_code == 200 else response.status_code
            worst = max(worst, max(timings))
            self.stdout.write(
                f"{name:<28}{found:>9}{statistics.median(timings):>13.1f}{max(timings):>10.1f}{len(ctx.captured_queries):>5}"
            )
        verdict = self.style.SUCCESS("OK") if worst < 2000 else self.style.ERROR("МЕДЛЕННО")
        self.stdout.write(f"Худший ответ: {worst:.1f} мс — требование < 2000 мс: {verdict}")
        self.worst_ms = worst
