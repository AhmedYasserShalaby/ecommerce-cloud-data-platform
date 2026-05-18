.PHONY: setup lint format-check test smoke generate run-all dashboard docker-config clean

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

lint:
	ruff check .

format-check:
	ruff format --check .

test:
	pytest --cov=src/commerce_platform --cov-report=term-missing

generate:
	commerce-platform generate-batch --profile ci

run-all:
	commerce-platform run-all --profile ci

smoke:
	commerce-platform smoke --profile ci

dashboard:
	streamlit run app/streamlit_console.py

docker-config:
	docker compose config

clean:
	rm -rf data/raw data/lake data/warehouse data/exports data/stream logs .pytest_cache .ruff_cache
