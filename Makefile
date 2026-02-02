.PHONY: help setup up down restart logs clean test

# ==============================================
# Calculadora de Consignados - Makefile
# ==============================================
# Comandos úteis para desenvolvimento

help: ## Mostrar esta ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup inicial do projeto (criar .env, instalar deps)
	@echo "🔧 Setup inicial..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Arquivo .env criado. EDITE com suas credenciais!"; \
	else \
		echo "⚠️  .env já existe"; \
	fi
	@echo "📦 Instalando dependências do backend..."
	@cd backend && pip install -e ".[dev]" || echo "⚠️  Instale manualmente: cd backend && pip install -e '.[dev]'"
	@echo "📦 Instalando dependências do frontend..."
	@cd frontend && npm install || echo "⚠️  Instale manualmente: cd frontend && npm install"
	@echo "✅ Setup concluído!"

up: ## Subir todos os serviços
	@echo "🚀 Subindo serviços..."
	docker-compose up -d
	@echo "⏳ Aguardando serviços ficarem prontos..."
	@sleep 5
	docker-compose ps
	@echo "✅ Serviços rodando!"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   Backend:   http://localhost:8000/docs"
	@echo "   MinIO:     http://localhost:9001"

down: ## Parar todos os serviços
	@echo "🛑 Parando serviços..."
	docker-compose down
	@echo "✅ Serviços parados!"

restart: down up ## Reiniciar todos os serviços

logs: ## Ver logs de todos os serviços
	docker-compose logs -f

logs-backend: ## Ver logs do backend
	docker-compose logs -f backend

logs-frontend: ## Ver logs do frontend
	docker-compose logs -f frontend

logs-worker: ## Ver logs do celery worker
	docker-compose logs -f celery-worker

ps: ## Ver status dos serviços
	docker-compose ps

shell-backend: ## Abrir shell no container do backend
	docker-compose exec backend bash

shell-frontend: ## Abrir shell no container do frontend
	docker-compose exec frontend sh

shell-db: ## Abrir psql no banco de dados
	docker-compose exec postgres psql -U postgres -d calculadora_consignados

migrate: ## Rodar migrations do banco
	@echo "🔄 Aplicando migrations..."
	docker-compose exec backend sh -lc "PYTHONPATH=/app alembic upgrade head"
	@echo "✅ Migrations aplicadas!"

migrate-create: ## Criar nova migration (use: make migrate-create MSG="descrição")
	@echo "📝 Criando migration..."
	docker-compose exec backend sh -lc "PYTHONPATH=/app alembic revision --autogenerate -m \"$(MSG)\""

migrate-down: ## Reverter última migration
	@echo "⏪ Revertendo migration..."
	docker-compose exec backend sh -lc "PYTHONPATH=/app alembic downgrade -1"

test-backend: ## Rodar testes do backend
	@echo "🧪 Rodando testes do backend..."
	cd backend && pytest -v --cov

test-frontend: ## Rodar testes do frontend
	@echo "🧪 Rodando testes do frontend..."
	cd frontend && npm run test

test: test-backend test-frontend ## Rodar todos os testes

lint-backend: ## Lint do backend
	@echo "🔍 Verificando código do backend..."
	cd backend && ruff check . && black --check .

lint-frontend: ## Lint do frontend
	@echo "🔍 Verificando código do frontend..."
	cd frontend && npm run lint

format-backend: ## Formatar código do backend
	@echo "✨ Formatando código do backend..."
	cd backend && black . && ruff check --fix .

format-frontend: ## Formatar código do frontend
	@echo "✨ Formatando código do frontend..."
	cd frontend && npm run format

clean: ## Limpar containers, volumes e cache
	@echo "🧹 Limpando..."
	docker-compose down -v
	@echo "✅ Limpeza concluída!"

reset: clean up migrate ## Reset completo (limpa tudo e recria)
	@echo "♻️  Reset completo realizado!"

build: ## Build das imagens Docker
	@echo "🏗️  Buildando imagens..."
	docker-compose build

prod-up: ## Subir em modo produção
	@echo "🚀 Subindo em modo PRODUÇÃO..."
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Parar modo produção
	docker-compose -f docker-compose.prod.yml down

backup-db: ## Backup do banco de dados
	@echo "💾 Fazendo backup do banco..."
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U postgres calculadora_consignados > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup salvo em backups/"

restore-db: ## Restaurar banco (use: make restore-db FILE=backup.sql)
	@echo "♻️  Restaurando banco de dados..."
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Erro: especifique o arquivo com FILE=backup.sql"; \
		exit 1; \
	fi
	docker-compose exec -T postgres psql -U postgres calculadora_consignados < $(FILE)
	@echo "✅ Banco restaurado!"

health: ## Verificar health dos serviços
	@echo "🏥 Verificando health..."
	@curl -s http://localhost:8000/health | jq . || echo "❌ Backend não está respondendo"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend OK" || echo "❌ Frontend não está respondendo"

dev-backend: ## Rodar backend em modo desenvolvimento (sem Docker)
	@echo "🔧 Rodando backend localmente..."
	cd backend && uvicorn app.main:app --reload

dev-frontend: ## Rodar frontend em modo desenvolvimento (sem Docker)
	@echo "🔧 Rodando frontend localmente..."
	cd frontend && npm run dev

.DEFAULT_GOAL := help
