setup:
	docker compose exec dagster-webserver bash -c "prisma generate && prisma migrate dev && python prisma/seed/seed.py"

up:
	docker compose up -d

down:
	docker compose down
