.PHONY: up down logs install seed events metrics agent smoke clean

up:            ## start Postgres + ClickHouse
	docker compose up -d

down:          ## stop the databases (keeps data)
	docker compose down

logs:
	docker compose logs -f --tail=50

install:       ## install Python deps into the current venv
	pip install -r requirements.txt

seed:          ## (re)seed Postgres with accounts + campaigns
	PYTHONPATH=src python -m converge.seed_oltp

events:        ## (re)generate + load ad events into ClickHouse
	PYTHONPATH=src python -m converge.generate_events

metrics:       ## time raw scan vs materialized rollup
	PYTHONPATH=src python -m converge.attribution

agent:         ## run the budget agent for real
	PYTHONPATH=src python -m converge.agent

agent-dry:     ## run the agent without writing changes
	PYTHONPATH=src python -m converge.agent --dry-run

smoke:         ## full end-to-end loop
	PYTHONPATH=src python -m converge.smoke_test

clean:         ## stop databases AND delete their data
	docker compose down -v
