"""Демо-данные для показа на контрольных точках.

Все люди, компании и резюме вымышленные (раздел 4 ТЗ: «в демо использовать только вымышленные резюме»).
Все адреса — на @demo.kg, у всех один пароль. Повторный запуск ничего не дублирует,
--reset удаляет только пользователей @demo.kg (вместе с их компаниями, вакансиями и резюме).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, User
from companies.models import Company, ModerationStatus
from profiles.models import Project, SeekerProfile
from resumes.models import Resume, Skill
from vacancies.models import Vacancy

DEMO_DOMAIN = "@demo.kg"
DEMO_PASSWORD = "Demo-Pass-2026"

APPROVED = ModerationStatus.APPROVED
PENDING = ModerationStatus.PENDING

COMPANIES = [
    {
        "owner": {"email": "employer@demo.kg", "full_name": "Жылдыз Асанова", "city": "Бишкек"},
        "name": "Тоо-Код",
        "city": "Бишкек",
        "description": "Вымышленная IT-компания: веб-разработка и мобильные приложения для бизнеса.",
        "website": "https://tookod.demo.kg",
        "contact_email": "hr@tookod.demo.kg",
        "moderation_status": APPROVED,
        "vacancies": [
            {
                "title": "Стажёр Python-разработчик",
                "city": "Бишкек",
                "salary_from": 15000,
                "salary_to": 25000,
                "experience": "none",
                "employment_type": "part",
                "schedule": "flexible",
                "is_internship": True,
                "skills": ["python", "django", "git"],
                "description": "Три месяца стажировки с наставником: REST API на Django, ревью кода, тесты.",
            },
            {
                "title": "Junior Frontend-разработчик (React)",
                "city": "Бишкек",
                "salary_from": 40000,
                "salary_to": 60000,
                "experience": "1-3",
                "employment_type": "full",
                "schedule": "full_day",
                "skills": ["javascript", "react", "css"],
                "description": "Разработка интерфейсов личных кабинетов клиентов на React.",
            },
            {
                "title": "Middle Backend-разработчик (Django)",
                "city": "Бишкек",
                "salary_from": 90000,
                "salary_to": 130000,
                "experience": "3-6",
                "employment_type": "full",
                "schedule": "remote",
                "skills": ["python", "django", "postgresql", "docker"],
                "description": "Проектирование API и оптимизация запросов к PostgreSQL.",
            },
            {
                "title": "QA-инженер (стажировка)",
                "city": "Бишкек",
                "salary_from": 12000,
                "experience": "none",
                "employment_type": "full",
                "schedule": "full_day",
                "is_internship": True,
                "skills": ["тестирование", "postman", "sql"],
                "description": "Ручное тестирование веб-приложений, написание тест-кейсов.",
            },
            {
                "title": "DevOps-инженер",
                "city": "Бишкек",
                "salary_from": 150000,
                "experience": "6+",
                "employment_type": "full",
                "schedule": "remote",
                "skills": ["docker", "kubernetes", "linux", "ci/cd"],
                "description": "Поддержка инфраструктуры и CI/CD для нескольких проектов.",
            },
            {
                "title": "Стажёр 1С-программист",
                "city": "Бишкек",
                "salary_from": 10000,
                "salary_to": 15000,
                "experience": "none",
                "employment_type": "part",
                "schedule": "full_day",
                "is_internship": True,
                "is_archived": True,
                "skills": ["1с"],
                "description": "Набор закрыт — вакансия в архиве.",
            },
        ],
    },
    {
        "owner": {"email": "employer2@demo.kg", "full_name": "Эрмек Касымов", "city": "Нарын"},
        "name": "Нарын Дата Лаб",
        "city": "Нарын",
        "description": "Вымышленная студия аналитики данных для агросектора и торговли.",
        "website": "https://narundata.demo.kg",
        "moderation_status": APPROVED,
        "vacancies": [
            {
                "title": "Стажёр-аналитик данных",
                "city": "Нарын",
                "salary_from": 10000,
                "salary_to": 15000,
                "experience": "none",
                "employment_type": "part",
                "schedule": "flexible",
                "is_internship": True,
                "skills": ["excel", "sql", "python"],
                "description": "Сбор и очистка данных, первые дашборды под присмотром аналитика.",
            },
            {
                "title": "Junior Data Analyst",
                "city": "Бишкек",
                "salary_from": 45000,
                "salary_to": 65000,
                "experience": "1-3",
                "employment_type": "full",
                "schedule": "full_day",
                "skills": ["sql", "python", "power bi"],
                "description": "Отчёты по продажам и прогноз спроса для клиентов студии.",
            },
            {
                "title": "Data Engineer",
                "city": "Бишкек",
                "experience": "3-6",
                "employment_type": "project",
                "schedule": "remote",
                "skills": ["python", "airflow", "postgresql"],
                "description": "Проект на полгода: построить ETL-конвейер. Зарплата по договорённости.",
            },
            {
                "title": "ML-инженер",
                "city": "Бишкек",
                "salary_from": 120000,
                "experience": "3-6",
                "employment_type": "full",
                "schedule": "remote",
                "moderation_status": PENDING,
                "skills": ["python", "pytorch"],
                "description": "Вакансия ждёт проверки администратором.",
            },
        ],
    },
    {
        "owner": {"email": "employer3@demo.kg", "full_name": "Гульнара Токтогулова", "city": "Каракол"},
        "name": "Каракол Тревел Тех",
        "city": "Каракол",
        "description": "Вымышленный сервис бронирования туров по Иссык-Кулю.",
        "website": "https://karakoltravel.demo.kg",
        "moderation_status": APPROVED,
        "vacancies": [
            {
                "title": "Менеджер по работе с клиентами (стажировка)",
                "city": "Каракол",
                "salary_from": 15000,
                "salary_to": 20000,
                "experience": "none",
                "employment_type": "full",
                "schedule": "shift",
                "is_internship": True,
                "skills": ["английский язык", "crm"],
                "description": "Летний сезон: консультации туристов, бронирования в CRM.",
            },
            {
                "title": "UI/UX-дизайнер",
                "city": "Каракол",
                "salary_from": 35000,
                "salary_to": 50000,
                "experience": "1-3",
                "employment_type": "project",
                "schedule": "flexible",
                "skills": ["figma", "ui/ux"],
                "description": "Редизайн мобильного приложения бронирования.",
            },
            {
                "title": "Мобильный разработчик (Flutter)",
                "city": "Бишкек",
                "salary_from": 70000,
                "salary_to": 100000,
                "experience": "1-3",
                "employment_type": "full",
                "schedule": "remote",
                "skills": ["flutter", "dart"],
                "description": "Развитие приложения для iOS и Android.",
            },
            {
                "title": "Контент-менеджер",
                "city": "Каракол",
                "salary_from": 20000,
                "salary_to": 30000,
                "experience": "none",
                "employment_type": "part",
                "schedule": "flexible",
                "skills": ["копирайтинг", "smm"],
                "description": "Описания туров и посты в соцсетях.",
            },
        ],
    },
    {
        "owner": {"email": "employer4@demo.kg", "full_name": "Бакыт Осмонов", "city": "Ош"},
        "name": "Ош Логистика Плюс",
        "city": "Ош",
        "description": "Вымышленная логистическая компания. Профиль ещё на модерации.",
        "moderation_status": PENDING,
        "vacancies": [
            {
                # одобрена, но не видна: компания ещё не прошла модерацию
                "title": "Диспетчер по перевозкам",
                "city": "Ош",
                "salary_from": 25000,
                "salary_to": 35000,
                "experience": "none",
                "employment_type": "full",
                "schedule": "shift",
                "skills": ["1с", "excel"],
                "description": "Планирование рейсов и связь с водителями.",
            },
        ],
    },
]

SEEKERS = [
    {
        "user": {"email": "seeker@demo.kg", "full_name": "Айбек Тестов", "city": "Бишкек", "phone": "+996 555 000 101"},
        "profile": {
            "about": "Студент 3 курса КГТУ, люблю backend и автоматизацию.",
            "github_url": "https://github.com/demo-aibek",
            "portfolio_url": "https://aibek.demo.kg",
        },
        "projects": [
            {
                "title": "Бот расписания КГТУ",
                "description": "Telegram-бот, который присылает расписание группы.",
                "url": "https://github.com/demo-aibek/schedule-bot",
                "technologies": "Python, aiogram, SQLite",
            },
            {
                "title": "Учёт библиотеки",
                "description": "Курсовая: REST API для выдачи книг.",
                "technologies": "Django, DRF, PostgreSQL",
            },
        ],
        "resume": {
            "title": "Junior Python-разработчик",
            "salary": 40000,
            "experience": "Стажировка 3 месяца в учебном центре.",
            "education": "КГТУ им. И. Раззакова, ПОВТ, 2027",
            "languages": ["кыргызский", "русский", "английский B1"],
            "skills": ["python", "django", "sql", "git"],
        },
    },
    {
        "user": {
            "email": "seeker2@demo.kg",
            "full_name": "Айгуль Примерова",
            "city": "Ош",
            "phone": "+996 555 000 102",
        },
        "profile": {
            "about": "Выпускница ОшГУ, делаю интерфейсы и немного дизайна.",
            "github_url": "https://github.com/demo-aigul",
        },
        "projects": [
            {
                "title": "Лендинг кофейни",
                "url": "https://github.com/demo-aigul/coffee-landing",
                "technologies": "React, CSS",
            },
            {"title": "Макет приложения для фитнеса", "technologies": "Figma"},
        ],
        "resume": {
            "title": "Frontend-разработчик",
            "salary": 50000,
            "education": "ОшГУ, прикладная информатика, 2026",
            "languages": ["кыргызский", "русский", "английский A2"],
            "skills": ["javascript", "react", "css", "figma"],
        },
    },
    {
        "user": {"email": "seeker3@demo.kg", "full_name": "Нурлан Образцов", "city": "Каракол"},
        "profile": {"about": "Студент экономического факультета, интересуюсь аналитикой данных."},
        "projects": [
            {
                "title": "Анализ цен на жильё в Бишкеке",
                "description": "Учебный проект на открытых вымышленных данных.",
                "technologies": "Python, pandas, Power BI",
            },
        ],
        "resume": {
            "title": "Стажёр-аналитик",
            "experience": "Без опыта, учебные проекты.",
            "education": "ИГУ им. К. Тыныстанова, экономика, 2028",
            "languages": ["кыргызский", "русский"],
            "skills": ["sql", "excel", "python", "power bi"],
        },
    },
]


class Command(BaseCommand):
    help = "Заполняет базу вымышленными демо-данными (все email на @demo.kg)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Сначала удалить всех пользователей @demo.kg и их данные"
        )

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        if reset:
            deleted, _ = User.objects.filter(email__iendswith=DEMO_DOMAIN).delete()
            self.stdout.write(f"Удалено демо-записей: {deleted}")

        self.user("admin@demo.kg", Role.ADMIN, full_name="Администратор", is_staff=True, is_superuser=True)
        for data in COMPANIES:
            self.company(data)
        for data in SEEKERS:
            self.seeker(data)

        self.stdout.write(
            self.style.SUCCESS(
                f"Демо-данные готовы: {Vacancy.objects.published().count()} опубликованных вакансий. "
                f"Вход: admin@demo.kg, employer@demo.kg, seeker@demo.kg — пароль {DEMO_PASSWORD}"
            )
        )

    def user(self, email, role, **fields):
        user, created = User.objects.get_or_create(
            email=email, defaults={"role": role, "email_verified": True, **fields}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save(update_fields=["password"])
        return user

    def company(self, data):
        data = dict(data)
        owner = self.user(role=Role.EMPLOYER, **data.pop("owner"))
        vacancies = data.pop("vacancies")
        company, _ = Company.objects.get_or_create(owner=owner, defaults=data)
        for item in vacancies:
            item = dict(item)
            skills = item.pop("skills")
            item.setdefault("moderation_status", APPROVED)
            vacancy, created = Vacancy.objects.get_or_create(company=company, title=item.pop("title"), defaults=item)
            if created:
                vacancy.skills.set(Skill.from_names(skills))

    def seeker(self, data):
        user = self.user(role=Role.SEEKER, **data["user"])
        profile, _ = SeekerProfile.objects.get_or_create(user=user, defaults=data["profile"])
        for item in data["projects"]:
            item = dict(item)
            Project.objects.get_or_create(profile=profile, title=item.pop("title"), defaults=item)

        resume_data = dict(data["resume"])
        skills = resume_data.pop("skills")
        resume_data.update(full_name=user.full_name, city=user.city, phone=user.phone, contact_email=user.email)
        title = resume_data.pop("title")
        resume, created = Resume.objects.get_or_create(seeker=user, title=title, defaults=resume_data)
        if created:
            resume.skills.set(Skill.from_names(skills))
