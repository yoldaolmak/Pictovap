.PHONY: install test lint clean demo help venv check-docs security-check

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
	@echo "  security-check  Run security hygiene tests"

demo:
	python3 -m pictovap.demo

install:
	python3 -m pip install -e ".[test,lint]"

test:
	python3 -m pytest tests/unit -v

check-docs:
	python3 -m pytest tests/unit/test_demo.py::test_docs_readme_links_resolve -v

lint:
	python3 -m flake8 src/ --max-line-length=120

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .pytest_cache .coverage

venv:
	python3 -m venv .venv

security-check:
	pytest tests/unit/test_security_hygiene.py -v
