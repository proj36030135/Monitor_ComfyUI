.PHONY: help install dev test lint format run clean migrate

# Configurações padrão
PYTHON := python
PIP := pip
UVICORN := uvicorn
PYTEST := pytest
BLACK := black
RUFF := ruff
ALEMBIC := alembic

# Variáveis de ambiente padrão
APP_HOST ?= 127.0.0.1
APP_PORT ?= 8080

help: ## Exibe esta mensagem de ajuda
	@echo "Backend de Observabilidade ComfyUI - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependências
	$(PIP) install -r requirements.txt

dev: install ## Configura ambiente de desenvolvimento
	@echo "Configurando ambiente de desenvolvimento..."
	$(ALEMBIC) upgrade head
	@echo "✅ Ambiente pronto para desenvolvimento"

test: ## Executa testes
	$(PYTEST) -v

test-cov: ## Executa testes com coverage
	$(PYTEST) --cov=app --cov-report=html --cov-report=term-missing tests/

lint: ## Executa linting com Ruff
	$(RUFF) check app/ alembic/

lint-fix: ## Executa linting com correção automática
	$(RUFF) check --fix app/ alembic/

format: ## Formata código com Black
	$(BLACK) app/ alembic/ tests/

format-check: ## Verifica formatação sem alterar arquivos
	$(BLACK) --check app/ alembic/ tests/

run: ## Executa servidor de desenvolvimento
	$(UVICORN) app.main:app --host $(APP_HOST) --port $(APP_PORT) --reload

run-prod: ## Executa servidor de produção
	$(UVICORN) app.main:app --host $(APP_HOST) --port $(APP_PORT) --workers 1

migrate: ## Cria nova migração
	$(ALEMBIC) revision --autogenerate -m "$(MESSAGE)"

migrate-up: ## Aplica migrações
	$(ALEMBIC) upgrade head

migrate-down: ## Reverte última migração
	$(ALEMBIC) downgrade -1

migrate-history: ## Mostra histórico de migrações
	$(ALEMBIC) history

clean: ## Remove arquivos temporários
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

clean-db: ## Remove banco de dados (cuidado!)
	rm -f app.db app.db-shm app.db-wal

reset-db: clean-db migrate-up ## Reset completo do banco de dados

check: lint format-check test ## Executa todas as verificações

all: clean install dev check ## Setup completo + verificações
