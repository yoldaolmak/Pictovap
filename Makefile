.PHONY: install test lint typecheck markdownlint quality contribution-check clean demo help venv check-docs security-check

help:
	@echo "Pictovap - Visual Finishing Engine"
	@echo ""
	@echo "Available targets:"
	@echo "  demo        Run the local credential-free demo"
	@echo "  test        Run test suite"
	@echo "  install     Install dependencies"
	@echo "  lint        Run code linters"
	@echo "  typecheck   Run static type checks"
	@echo "  markdownlint Check Markdown structure"
	@echo "  quality     Run all local quality gates"
	@echo "  contribution-check  Run the fast contributor gates (no Node/npm)"
	@echo "  clean       Clean temporary files"
	@echo "  venv        Create virtual environment"
	@echo "  check-docs  Check documentation link integrity"
	@echo "  security-check  Run security hygiene tests"

demo:
	python3 -m pictovap.demo

install:
	python3 -m pip install -e ".[test,lint,typecheck]"

test:
	python3 -m pytest tests/unit -v

check-docs:
	python3 -m pytest --no-cov tests/unit/test_demo.py::test_docs_readme_links_resolve -v

lint:
	python3 -m flake8 src/ --max-line-length=120

typecheck:
	python3 -m pyright

markdownlint:
	npx --yes markdownlint-cli2@0.23.0 --config .markdownlint.json 'README.md' 'CONTRIBUTING.md' 'SECURITY.md' 'CODE_OF_CONDUCT.md' 'CHANGELOG.md' 'docs/**/*.md' 'examples/**/*.md' 'src/pictovap/**/*.md' 'tests/**/*.md'

quality: lint typecheck markdownlint test

contribution-check: lint typecheck test check-docs security-check

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .pytest_cache .coverage

venv:
	python3 -m venv .venv

security-check:
	pytest --no-cov tests/unit/test_security_hygiene.py -v
