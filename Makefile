# StoraTrack - Makefile para tareas de desarrollo y despliegue

# Variables
PYTHON := python
PIP := pip
DOCKER := docker
DOCKER_COMPOSE := docker-compose
APP_NAME := storatrack
DB_NAME := storatrack_db

# Colores para output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

.PHONY: help install dev prod test clean docker-build docker-up docker-down docker-logs db-init db-seed db-reset backup lint format check-deps security

# Ayuda por defecto
help:
	@echo "$(BLUE)StoraTrack - Sistema de Gestión de Inventario$(RESET)"
	@echo ""
	@echo "$(YELLOW)Comandos disponibles:$(RESET)"
	@echo "  $(GREEN)install$(RESET)      - Instalar dependencias"
	@echo "  $(GREEN)dev$(RESET)          - Ejecutar en modo desarrollo"
	@echo "  $(GREEN)prod$(RESET)         - Ejecutar en modo producción"
	@echo "  $(GREEN)test$(RESET)         - Ejecutar tests"
	@echo "  $(GREEN)clean$(RESET)        - Limpiar archivos temporales"
	@echo ""
	@echo "$(YELLOW)Docker:$(RESET)"
	@echo "  $(GREEN)docker-build$(RESET) - Construir imagen Docker"
	@echo "  $(GREEN)docker-up$(RESET)    - Levantar servicios con Docker Compose"
	@echo "  $(GREEN)docker-down$(RESET)  - Detener servicios Docker"
	@echo "  $(GREEN)docker-logs$(RESET)  - Ver logs de Docker"
	@echo ""
	@echo "$(YELLOW)Base de datos:$(RESET)"
	@echo "  $(GREEN)db-init$(RESET)      - Inicializar base de datos"
	@echo "  $(GREEN)db-seed$(RESET)      - Poblar con datos de ejemplo"
	@echo "  $(GREEN)db-reset$(RESET)     - Resetear base de datos"
	@echo "  $(GREEN)backup$(RESET)       - Crear backup de la base de datos"
	@echo ""
	@echo "$(YELLOW)Calidad de código:$(RESET)"
	@echo "  $(GREEN)lint$(RESET)         - Ejecutar linting"
	@echo "  $(GREEN)format$(RESET)       - Formatear código"
	@echo "  $(GREEN)security$(RESET)     - Análisis de seguridad"
	@echo "  $(GREEN)check-deps$(RESET)   - Verificar dependencias"

# Instalación de dependencias
install:
	@echo "$(BLUE)Instalando dependencias...$(RESET)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencias instaladas$(RESET)"

install-dev:
	@echo "$(BLUE)Instalando dependencias de desarrollo...$(RESET)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-cov black flake8 isort bandit safety
	@echo "$(GREEN)✓ Dependencias de desarrollo instaladas$(RESET)"

# Desarrollo
dev:
	@echo "$(BLUE)Iniciando servidor de desarrollo...$(RESET)"
	@if not exist ".env" (
		echo "$(YELLOW)⚠ Archivo .env no encontrado. Copiando desde .env.example...$(RESET)" && \
		copy .env.example .env
	)
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Producción
prod:
	@echo "$(BLUE)Iniciando servidor de producción...$(RESET)"
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Tests
test:
	@echo "$(BLUE)Ejecutando tests...$(RESET)"
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Tests completados$(RESET)"

test-fast:
	@echo "$(BLUE)Ejecutando tests rápidos...$(RESET)"
	pytest tests/ -x -q

# Limpieza
clean:
	@echo "$(BLUE)Limpiando archivos temporales...$(RESET)"
	@if exist "__pycache__" rmdir /s /q __pycache__
	@if exist ".pytest_cache" rmdir /s /q .pytest_cache
	@if exist "htmlcov" rmdir /s /q htmlcov
	@if exist ".coverage" del .coverage
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"
	@echo "$(GREEN)✓ Archivos temporales eliminados$(RESET)"

# Docker
docker-build:
	@echo "$(BLUE)Construyendo imagen Docker...$(RESET)"
	$(DOCKER) build -t $(APP_NAME) .
	@echo "$(GREEN)✓ Imagen Docker construida$(RESET)"

docker-up:
	@echo "$(BLUE)Levantando servicios con Docker Compose...$(RESET)"
	@if not exist ".env" (
		echo "$(YELLOW)⚠ Archivo .env no encontrado. Copiando desde .env.example...$(RESET)" && \
		copy .env.example .env
	)
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Servicios levantados$(RESET)"
	@echo "$(YELLOW)Aplicación disponible en: http://localhost:8000$(RESET)"

docker-up-build:
	@echo "$(BLUE)Construyendo y levantando servicios...$(RESET)"
	$(DOCKER_COMPOSE) up -d --build
	@echo "$(GREEN)✓ Servicios construidos y levantados$(RESET)"

docker-down:
	@echo "$(BLUE)Deteniendo servicios Docker...$(RESET)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Servicios detenidos$(RESET)"

docker-down-volumes:
	@echo "$(BLUE)Deteniendo servicios y eliminando volúmenes...$(RESET)"
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✓ Servicios y volúmenes eliminados$(RESET)"

docker-logs:
	@echo "$(BLUE)Mostrando logs de Docker...$(RESET)"
	$(DOCKER_COMPOSE) logs -f

docker-logs-app:
	@echo "$(BLUE)Mostrando logs de la aplicación...$(RESET)"
	$(DOCKER_COMPOSE) logs -f web

docker-shell:
	@echo "$(BLUE)Accediendo al shell del contenedor...$(RESET)"
	$(DOCKER_COMPOSE) exec web bash

# Base de datos
db-init:
	@echo "$(BLUE)Inicializando base de datos...$(RESET)"
	$(PYTHON) app/init_db.py
	@echo "$(GREEN)✓ Base de datos inicializada$(RESET)"

db-seed:
	@echo "$(BLUE)Poblando base de datos con datos de ejemplo...$(RESET)"
	$(PYTHON) app/seeds.py
	@echo "$(GREEN)✓ Datos de ejemplo cargados$(RESET)"

db-reset:
	@echo "$(YELLOW)⚠ Esto eliminará todos los datos. ¿Continuar? [y/N]$(RESET)"
	@set /p confirm=""
	@if /i "!confirm!"=="y" (
		echo "$(BLUE)Reseteando base de datos...$(RESET)" && \
		$(PYTHON) app/init_db.py --reset && \
		$(PYTHON) app/seeds.py && \
		echo "$(GREEN)✓ Base de datos reseteada$(RESET)"
	) else (
		echo "$(YELLOW)Operación cancelada$(RESET)"
	)

db-migrate:
	@echo "$(BLUE)Ejecutando migraciones...$(RESET)"
	@echo "$(YELLOW)⚠ Funcionalidad de migraciones no implementada aún$(RESET)"

# Backup
backup:
	@echo "$(BLUE)Creando backup de la base de datos...$(RESET)"
	@if not exist "backups" mkdir backups
	@set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
	@set timestamp=!timestamp: =0!
	pg_dump $(DB_NAME) > backups/backup_!timestamp!.sql
	@echo "$(GREEN)✓ Backup creado en backups/backup_!timestamp!.sql$(RESET)"

restore:
	@echo "$(BLUE)Restaurando backup...$(RESET)"
	@echo "$(YELLOW)Especifica el archivo de backup:$(RESET)"
	@set /p backup_file=""
	@if exist "!backup_file!" (
		psql $(DB_NAME) < "!backup_file!" && \
		echo "$(GREEN)✓ Backup restaurado$(RESET)"
	) else (
		echo "$(RED)❌ Archivo de backup no encontrado$(RESET)"
	)

# Calidad de código
lint:
	@echo "$(BLUE)Ejecutando linting...$(RESET)"
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(GREEN)✓ Linting completado$(RESET)"

format:
	@echo "$(BLUE)Formateando código...$(RESET)"
	black app/ --line-length=88
	isort app/ --profile black
	@echo "$(GREEN)✓ Código formateado$(RESET)"

format-check:
	@echo "$(BLUE)Verificando formato del código...$(RESET)"
	black app/ --check --line-length=88
	isort app/ --check-only --profile black

# Seguridad
security:
	@echo "$(BLUE)Ejecutando análisis de seguridad...$(RESET)"
	bandit -r app/ -f json -o security-report.json
	safety check --json --output safety-report.json
	@echo "$(GREEN)✓ Análisis de seguridad completado$(RESET)"

# Dependencias
check-deps:
	@echo "$(BLUE)Verificando dependencias...$(RESET)"
	pip list --outdated
	@echo "$(GREEN)✓ Verificación de dependencias completada$(RESET)"

update-deps:
	@echo "$(BLUE)Actualizando dependencias...$(RESET)"
	pip list --outdated --format=freeze | findstr "=" > outdated.txt
	@echo "$(YELLOW)Dependencias desactualizadas guardadas en outdated.txt$(RESET)"
	@echo "$(YELLOW)Revisa manualmente antes de actualizar$(RESET)"

freeze-deps:
	@echo "$(BLUE)Generando requirements.txt actualizado...$(RESET)"
	pip freeze > requirements-new.txt
	@echo "$(GREEN)✓ Dependencias guardadas en requirements-new.txt$(RESET)"

# Documentación
docs:
	@echo "$(BLUE)Generando documentación...$(RESET)"
	@echo "$(YELLOW)⚠ Funcionalidad de documentación no implementada aún$(RESET)"

# Monitoreo
status:
	@echo "$(BLUE)Estado de los servicios:$(RESET)"
	$(DOCKER_COMPOSE) ps

health:
	@echo "$(BLUE)Verificando salud de la aplicación...$(RESET)"
	curl -f http://localhost:8000/health || echo "$(RED)❌ Aplicación no responde$(RESET)"

# Utilidades
shell:
	@echo "$(BLUE)Iniciando shell de Python con contexto de la aplicación...$(RESET)"
	$(PYTHON) -i -c "from app.database import SessionLocal; from app.models import *; db = SessionLocal()"

reset-env:
	@echo "$(BLUE)Reseteando archivo de entorno...$(RESET)"
	@if exist ".env" del .env
	copy .env.example .env
	@echo "$(GREEN)✓ Archivo .env reseteado desde .env.example$(RESET)"

# Instalación completa
setup:
	@echo "$(BLUE)Configuración inicial completa...$(RESET)"
	@$(MAKE) install-dev
	@$(MAKE) reset-env
	@$(MAKE) docker-up-build
	@timeout /t 10 /nobreak > nul
	@$(MAKE) db-init
	@$(MAKE) db-seed
	@echo "$(GREEN)✅ Configuración completa!$(RESET)"
	@echo "$(YELLOW)Aplicación disponible en: http://localhost:8000$(RESET)"
	@echo "$(YELLOW)Credenciales: admin@storatrack.com / admin123$(RESET)"

# Desinstalación
teardown:
	@echo "$(YELLOW)⚠ Esto eliminará todos los contenedores y volúmenes. ¿Continuar? [y/N]$(RESET)"
	@set /p confirm=""
	@if /i "!confirm!"=="y" (
		echo "$(BLUE)Eliminando todo...$(RESET)" && \
		$(MAKE) docker-down-volumes && \
		$(DOCKER) system prune -f && \
		echo "$(GREEN)✓ Limpieza completa$(RESET)"
	) else (
		echo "$(YELLOW)Operación cancelada$(RESET)"
	)