.PHONY: up down logs restart check

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

restart:
	docker compose restart

check:
	python -m compileall -q app
