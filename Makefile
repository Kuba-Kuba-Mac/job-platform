.PHONY: up down logs test lint superuser migrations shell seed reseed secret

up:            ## Запустить всё (db + backend + frontend)
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f backend

test:          ## Автотесты backend
	docker compose run --rm backend python manage.py test

lint:
	docker compose run --rm backend ruff check .

superuser:     ## Создать администратора
	docker compose run --rm backend python manage.py createsuperuser

migrations:    ## Создать миграции после изменения моделей
	docker compose run --rm backend python manage.py makemigrations

shell:
	docker compose run --rm backend python manage.py shell

seed:          ## Добавить вымышленные демо-данные (@demo.kg), без дублей
	docker compose run --rm backend python manage.py seed_demo

reseed:        ## Удалить демо-данные @demo.kg и создать заново
	docker compose run --rm backend python manage.py seed_demo --reset

secret:        ## Сгенерировать DJANGO_SECRET_KEY для .env
	@python3 -c "import secrets; print(secrets.token_urlsafe(50))"
