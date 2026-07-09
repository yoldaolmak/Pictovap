.PHONY: install test lint clean demo help venv check-docs

help:
	@echo "Pictovap - Visual Finishing Engine"
	@echo ""
	@echo "Available targets:"
	@echo "  demo        Run the local credential-free demo"
	@echo "  test        Run test suite"
	@echo "  install     Install dependencies"
	@echo "  lint        Run code linters"
	@echo "  clean       Clean temporary files"
	@echo "  venv        Create virtual environment"
	@echo "  check-docs  Check documentation link integrity"

demo:
	python3 -m pictova.demo

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/unit -v

check-docs:
	pytest tests/unit/test_docs.py -v

lint:
	flake8 src/ --max-line-length=120

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage

venv:
	python3 -m venv .venv

check-docs:
	pytest tests/unit/test_demo.py::test_docs_readme_links_resolve -v
