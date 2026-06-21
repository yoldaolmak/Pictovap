# VIL - Visual Intelligence Layer
# Premium Startup Makefile

.PHONY: install test lint clean run help docs format test-cov venv

help:
	@echo "VIL - Visual Intelligence Layer"
	@echo ""
	@echo "Available targets:"
	@echo "  install    Install all dependencies"
	@echo "  test       Run test suite"
	@echo "  test-cov   Run tests with coverage report"
	@echo "  lint       Run code linters"
	@echo "  format     Format code with black"
	@echo "  clean      Clean temporary files"
	@echo "  run        Run the orchestrator (requires POST_ID)"
	@echo "  docs       Generate documentation"
	@echo "  venv       Create virtual environment"

install:
	pip install -r requirements.txt

test:
	pytest tests/unit -v

test-cov:
	pytest tests/unit -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	flake8 src/ --max-line-length=120
	black --check src/

format:
	black src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/

run:
	@if [ -z "$(POST_ID)" ]; then \
		echo "Usage: make run POST_ID=<post_id>"; \
		exit 1; \
	fi
	python -m src.core.yo_orchestrator --post-id $(POST_ID)

venv:
	python -m venv venv

docs:
	ls -la docs/
