.PHONY: install lint typecheck test check

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

typecheck:
	mypy src

test:
	pytest --cov=envguard --cov-report=term-missing

check: lint typecheck test
