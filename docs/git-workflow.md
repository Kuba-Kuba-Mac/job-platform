# Работа с репозиторием

## 1. Создание репозитория (делает Участник 1, один раз)

1. На GitHub: **New repository** → имя `job-platform` → Private или Public → **без** README (он уже есть).
2. Залить код из этого архива:

   ```bash
   cd job-platform
   git init -b main
   git add .
   git commit -m "chore: каркас проекта (Django + React + Docker + CI)"
   git remote add origin https://github.com/<владелец>/job-platform.git
   git push -u origin main

   git checkout -b develop
   git push -u origin develop
   ```

3. **Settings → Collaborators** — пригласить Участника 2 и Участника 3.
4. **Settings → General → Default branch** — оставить `main`.
5. **Settings → Branches → Add branch ruleset** (или Branch protection rules) для `main` и `develop`:
   - Require a pull request before merging, 1 approval;
   - Require status checks to pass → выбрать `backend` и `frontend` (появятся после первого запуска CI);
   - Block force pushes.
6. **Projects → New project → Board**: колонки `Backlog`, `To do`, `In progress`, `Review`, `Done`.
   Создать issue на каждую функцию из ТЗ по шаблону «Функция из ТЗ», добавить их на доску.
7. **Issues → Milestones**: пять контрольных точек — `КТ1 20% (01.11)`, `КТ2 40% (15.11)`, `КТ3 60% (01.12)`, `КТ4 80% (15.12)`, `КТ5 100% (30.12)`.

## 2. Ветки

```
main       ← стабильная версия, сдаётся на контрольных точках
develop    ← общая разработка, сюда сливаются все задачи
feature/F-01-registration
feature/E-01-company-profile
fix/resume-salary-validation
```

Одна функция — одна ветка, одна ветка — один pull request.

## 3. Ежедневный цикл

```bash
git checkout develop && git pull
git checkout -b feature/E-02-vacancies
# ... работа ...
git add -p
git commit -m "feat(vacancies): создание и архивация вакансий (E-02)"
git push -u origin feature/E-02-vacancies
```

Затем на GitHub: **Pull request → base: develop**, заполнить шаблон, назначить ревьюера. После одобрения и зелёного CI — **Squash and merge**.

На контрольной точке: PR `develop → main` и тег `v0.1` (20%), `v0.2` (40%) и т. д.

## 4. Сообщения коммитов

Формат: `тип(область): что сделано (номер в ТЗ)`

| Тип | Когда |
|---|---|
| `feat` | новая функция |
| `fix` | исправление ошибки |
| `test` | тесты |
| `docs` | документация |
| `refactor` | переделка без изменения поведения |
| `chore` | настройка, зависимости, CI |

Примеры: `feat(auth): вход по JWT (F-02)`, `test(resumes): проверка доступа к чужому резюме (S-01)`.

## 5. Code review

- Каждый PR смотрит хотя бы один другой участник.
- Проверяем: работает ли, есть ли тесты, проверяются ли права на сервере, нет ли секретов в коде.
- Замечания пишем конкретно, со ссылкой на строку.

## 6. Если изменили модели

```bash
make migrations          # или: python manage.py makemigrations
```

Миграции коммитятся вместе с моделями. CI упадёт, если миграции забыли.
