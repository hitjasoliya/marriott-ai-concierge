.PHONY: dev seed embed reset

dev:
	docker compose up --build

seed:
	docker compose exec backend python -m app.seed.seeder

embed:
	docker compose exec backend python -m app.embeddings.pipeline

reset:
	docker compose down -v
	docker compose up --build
