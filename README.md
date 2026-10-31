# Стажировки KG — платформа поиска работы и стажировок

Веб-приложение для студентов, выпускников и местных компаний: соискатель ведёт резюме и откликается на вакансии, работодатель публикует вакансии и обрабатывает отклики.

Групповой проект, команда из 3 человек.

## Стек

| Слой | Технологии |
|---|---|
| Backend | Django 5 + Django REST Framework, JWT (simplejwt), Argon2 |
| База данных | PostgreSQL 16 |
| Frontend | React 18 + Vite |
| Инфраструктура | Docker Compose, GitHub Actions |
| Документация API | Swagger (drf-spectacular) |

## Быстрый старт (одной командой)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000/api/
- Swagger: http://localhost:8000/api/docs/
- Админка Django: http://localhost:8000/admin/ (создать админа: `make superuser`)

### Без Docker (только backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate        # без POSTGRES_HOST используется SQLite
python manage.py test
python manage.py runserver
```

## Структура репозитория

```
backend/
  config/      настройки Django, корневые URL
  accounts/    пользователи, роли, регистрация, JWT  (F-01, F-02, F-03, F-06)
  companies/   профиль компании                       (E-01)
  resumes/     резюме и справочник навыков            (S-01)
frontend/
  src/pages/   страницы: вход, регистрация, компания, резюме
.github/       CI, шаблоны pull request и issues
docs/          правила работы с Git, диаграммы
```

## Готовность: контрольная точка 1 (20%, 01.11.2026)

| № | Функция | Участник | Статус |
|---|---|---|---|
| F-01 | Регистрация по email и паролю с выбором роли | Участник 1 | ✅ |
| F-02 | Вход и выход, JWT (access + refresh, отзыв при выходе) | Участник 1 | ✅ |
| F-03 | Смена пароля в личном кабинете (старый / новый / повтор), индикатор надёжности (слабый / средний / надёжный) и список правил при регистрации и смене пароля | Участник 1 | ✅ |
| F-06 | Интерфейс по ролям: своё меню и личный кабинет у каждой роли; на странице чужой роли — «Недоступно для вашей роли» (права проверяются и на сервере) | Участник 1 | ✅ |
| E-01 | Профиль компании | Участник 2 | ✅ |
| S-01 | Создание и редактирование резюме | Участник 3 | ✅ |
| — | Репозиторий, Docker, CI | Участник 1 | ✅ |

## API (этап 1)

| Метод | URL | Кто | Описание |
|---|---|---|---|
| POST | `/api/auth/register/` | все | регистрация `{email, password, role}` |
| POST | `/api/auth/login/` | все | вход → `{access, refresh, user}` |
| POST | `/api/auth/refresh/` | все | обновить access-токен |
| POST | `/api/auth/logout/` | авторизованный | выход, refresh в чёрный список |
| GET | `/api/auth/me/` | авторизованный | текущий пользователь |
| POST | `/api/auth/password/change/` | авторизованный | смена пароля `{old_password, new_password}` → новая пара `{access, refresh}`, старые refresh отзываются |
| GET | `/api/companies/` | все | одобренные компании |
| GET/POST/PATCH | `/api/companies/me/` | работодатель | свой профиль компании |
| GET/POST | `/api/resumes/` | соискатель | свои резюме |
| GET/PATCH/DELETE | `/api/resumes/{id}/` | соискатель | одно своё резюме |
| GET | `/api/skills/?q=py` | все | подсказки навыков |

Полное описание — в Swagger: `/api/docs/`.

## Команда и зоны ответственности

| Участник | Функции | Общие задачи |
|---|---|---|
| Участник 1 | F-01…F-06, A-01…A-03, N-01, N-02 | репозиторий, CI/CD, Docker, деплой |
| Участник 2 | E-01…E-06, S-04, S-05, X-03, X-05, X-06 | схема БД, ER-диаграмма, README, Swagger |
| Участник 3 | S-01…S-03, S-06…S-08, X-01, X-02, X-04, N-03 | макеты, тестовые данные, сценарий демо |

## Как мы работаем

Правила веток, коммитов и pull request — в [docs/git-workflow.md](docs/git-workflow.md).
