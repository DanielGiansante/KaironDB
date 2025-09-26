# KaironDB Makefile

.PHONY: help install install-dev test test-cov lint format clean build docs

help: ## Show this help message
	@echo "KaironDB - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install KaironDB
	pip install -e .

install-dev: ## Install KaironDB with development dependencies
	pip install -e .[dev]

test: ## Run tests
	python -m pytest tests/ -v

test-cov: ## Run tests with coverage
	python -m pytest tests/ -v --cov=src/kairondb --cov-report=html --cov-report=term

lint: ## Run linting
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python setup.py sdist bdist_wheel

docs: ## Build documentation
	cd docs && python -m http.server 8000

# Development workflow
dev-setup: install-dev ## Setup development environment
	pre-commit install

dev-test: format lint test ## Run full development test suite

# Quick tests
quick-test: ## Run quick tests (no coverage)
	python -m pytest tests/ -v --tb=short

# Specific test modules
test-bridge: ## Test bridge module
	python -m pytest tests/test_bridge.py -v

test-models: ## Test models module
	python -m pytest tests/test_models.py -v

test-exceptions: ## Test exceptions module
	python -m pytest tests/test_exceptions.py -v

test-logging: ## Test logging module
	python -m pytest tests/test_logging.py -v

test-queries: ## Test queries module
	python -m pytest tests/test_query.py -v
