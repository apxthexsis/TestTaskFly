.PHONY: assignment quality unit

assignment:
	bash ./run-assignment.sh

quality:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src

unit:
	uv run pytest tests/unit

