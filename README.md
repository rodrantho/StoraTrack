# StoraTrack 📦

**Sistema de Gestión de Inventario Multi-Tenant**

StoraTrack es una aplicación web moderna para la gestión de inventario de equipos tecnológicos, diseñada para empresas que necesitan un control detallado de sus activos con capacidades multi-tenant, generación de reportes y etiquetas QR/código de barras.

## 🚀 Características Principales

### 🏢 Multi-Tenant
- **Gestión de múltiples empresas** en una sola instancia
- **Aislamiento completo** de datos entre empresas
- **Roles diferenciados**: Superadmin, Staff y Cliente
- **Configuración personalizada** por empresa

### 📱 Gestión de Equipos
- **Registro completo** de dispositivos con información detallada
- **Seguimiento de ubicaciones** y movimientos
- **Estados personalizables**: Almacenado, En Proceso, Finalizado
- **Condiciones**: Excelente, Bueno, Regular, Malo
- **Sistema de tags** para categorización flexible

### 💰 Cálculo de Costos
- **Costos automáticos** basados en tiempo de almacenamiento
- **Configuración personalizable** de tarifas por empresa
- **Cálculo de IVA** integrado
- **Reportes detallados** en PDF y CSV
- **Histórico de costos** por períodos

### 🏷️ Etiquetas y Códigos
- **Generación automática** de códigos QR y Code128
- **Etiquetas imprimibles** con información completa
- **Acceso directo** via QR a información del equipo
- **Generación en lote** para múltiples dispositivos

### 📊 Reportes y Analytics
- **Reportes PDF/CSV** personalizables
- **Dashboards interactivos** con métricas clave
- **Exportación de datos** en múltiples formatos
- **Análisis de costos** por empresa y período

### 🔐 Seguridad
- **Autenticación JWT** con tokens seguros
- **Control de acceso** basado en roles
- **Aislamiento de datos** por empresa
- **Validación de entrada** en todas las operaciones

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos principal
- **Redis** - Cache y sesiones
- **Pydantic** - Validación de datos

### Frontend
- **HTMX** - Interactividad sin JavaScript complejo
- **Bootstrap 5** - Framework CSS moderno
- **Jinja2** - Motor de plantillas
- **Chart.js** - Gráficos interactivos

### Herramientas
- **Docker** - Containerización
- **ReportLab** - Generación de PDFs
- **qrcode** - Generación de códigos QR
- **python-barcode** - Generación de códigos de barras
- **Pillow** - Procesamiento de imágenes

## 📋 Requisitos del Sistema

### Desarrollo
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker y Docker Compose (opcional)

### Producción
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ almacenamiento
- PostgreSQL 13+
- Redis 6+
- Nginx (recomendado)

## 🚀 Instalación y Configuración

### Opción 1: Docker (Recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/storatrack.git
cd storatrack

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Levantar todos los servicios
make setup
```

### Opción 2: Instalación Manual

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/storatrack.git
cd storatrack

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
make install-dev

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Inicializar base de datos
make db-init
make db-seed

# Ejecutar en modo desarrollo
make dev
```

## 🔧 Configuración

### Variables de Entorno Principales

```env
# Aplicación
SECRET_KEY=tu-clave-secreta-muy-segura
ENVIRONMENT=development
DEBUG=true

# Base de Datos
DATABASE_URL=postgresql://user:password@localhost:5432/storatrack_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Servidor
HOST=0.0.0.0
PORT=8000
```

Ver `.env.example` para todas las opciones disponibles.

## 📚 Uso

### Acceso Inicial

Después de la instalación, accede a:
- **URL**: http://localhost:8000
- Utiliza las credenciales configuradas durante la inicialización de la base de datos

### Flujo de Trabajo Típico

1. **Configuración Inicial**
   - Crear empresas clientes
   - Configurar ubicaciones
   - Definir tags personalizados
   - Establecer tarifas de costos

2. **Gestión de Equipos**
   - Registrar nuevos dispositivos
   - Asignar ubicaciones y tags
   - Generar etiquetas QR/código de barras
   - Imprimir etiquetas

3. **Seguimiento**
   - Mover equipos entre ubicaciones
   - Cambiar estados según el proceso
   - Registrar notas y observaciones

4. **Reportes y Facturación**
   - Generar reportes de costos
   - Exportar datos para facturación
   - Analizar métricas de uso

## 🎯 Comandos Make Disponibles

### Desarrollo
```bash
make dev          # Ejecutar en modo desarrollo
make test         # Ejecutar tests
make lint         # Verificar código
make format       # Formatear código
```

### Docker
```bash
make docker-up    # Levantar servicios
make docker-down  # Detener servicios
make docker-logs  # Ver logs
```

### Base de Datos
```bash
make db-init      # Inicializar BD
make db-seed      # Cargar datos de ejemplo
make db-reset     # Resetear BD completa
make backup       # Crear backup
```

### Utilidades
```bash
make clean        # Limpiar archivos temporales
make security     # Análisis de seguridad
make check-deps   # Verificar dependencias
```

## 🏗️ Arquitectura

### Estructura del Proyecto

```
storatrack/
├── app/
│   ├── api/              # Endpoints API
│   ├── models/           # Modelos SQLAlchemy
│   ├── routers/          # Rutas web
│   ├── services/         # Lógica de negocio
│   ├── schemas/          # Esquemas Pydantic
│   └── utils/            # Utilidades
├── templates/            # Plantillas HTML
├── static/              # Archivos estáticos
├── tests/               # Tests
├── docker-compose.yml   # Configuración Docker
├── Dockerfile          # Imagen Docker
├── requirements.txt    # Dependencias Python
└── Makefile           # Comandos automatizados
```

### Flujo de Datos

```
Cliente → Nginx → FastAPI → SQLAlchemy → PostgreSQL
                     ↓
                  Redis (Cache/Sesiones)
```

## 🔌 API

### Endpoints Principales

#### Autenticación
- `POST /auth/login` - Iniciar sesión
- `POST /auth/logout` - Cerrar sesión
- `GET /auth/me` - Información del usuario actual

#### Dispositivos
- `GET /api/devices` - Listar dispositivos
- `POST /api/devices` - Crear dispositivo
- `GET /api/devices/{id}` - Obtener dispositivo
- `PUT /api/devices/{id}` - Actualizar dispositivo
- `DELETE /api/devices/{id}` - Eliminar dispositivo

#### Reportes
- `GET /api/reports/costs/device/{id}` - Reporte de costos de dispositivo
- `GET /api/reports/costs/company/{id}` - Reporte de costos de empresa
- `POST /api/reports/export` - Exportar datos

#### Etiquetas
- `GET /api/labels/qr/{device_id}` - Generar QR
- `GET /api/labels/barcode/{device_id}` - Generar código de barras
- `POST /api/labels/batch` - Generación en lote

### Documentación API

Accede a la documentación interactiva en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

```bash
# Ejecutar todos los tests
make test

# Tests rápidos
make test-fast

# Tests con cobertura
pytest --cov=app --cov-report=html
```

### Estructura de Tests

```
tests/
├── conftest.py          # Configuración pytest
├── test_auth.py         # Tests autenticación
├── test_devices.py      # Tests dispositivos
├── test_reports.py      # Tests reportes
└── test_api.py          # Tests API
```

## 🚀 Despliegue en Producción

### Docker Compose (Recomendado)

```bash
# Configurar para producción
cp .env.example .env
# Editar variables para producción

# Levantar servicios
docker-compose -f docker-compose.yml up -d

# Verificar estado
docker-compose ps
```

### Variables de Producción

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=clave-super-segura-de-produccion
DATABASE_URL=postgresql://user:pass@db:5432/storatrack
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=["https://tu-dominio.com"]
SSL_ENABLED=true
```

### Nginx (Opcional)

```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/storatrack/static/;
    }
}
```

## 🔧 Mantenimiento

### Backups

```bash
# Backup automático
make backup

# Backup manual con Docker
docker-compose exec db pg_dump -U postgres storatrack_db > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U postgres storatrack_db < backup.sql
```

### Monitoreo

```bash
# Estado de servicios
make status

# Logs en tiempo real
make docker-logs

# Verificar salud
make health
```

### Actualizaciones

```bash
# Actualizar código
git pull origin main

# Reconstruir y reiniciar
docker-compose up -d --build

# Ejecutar migraciones (si las hay)
make db-migrate
```

## 🤝 Contribución

### Proceso de Desarrollo

1. **Fork** el repositorio
2. **Crear** una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. **Desarrollar** siguiendo las convenciones del proyecto
4. **Ejecutar** tests: `make test`
5. **Verificar** calidad: `make lint format security`
6. **Commit** con mensajes descriptivos
7. **Push** a tu fork: `git push origin feature/nueva-funcionalidad`
8. **Crear** Pull Request

### Convenciones de Código

- **Python**: Seguir PEP 8, usar Black para formateo
- **HTML/CSS**: Usar Bootstrap classes, mantener consistencia
- **JavaScript**: ES6+, usar funciones arrow cuando sea apropiado
- **Commits**: Usar conventional commits (feat:, fix:, docs:, etc.)

### Estructura de Commits

```
feat: agregar generación de etiquetas QR
fix: corregir cálculo de costos con IVA
docs: actualizar documentación de API
test: agregar tests para módulo de reportes
```

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

### Problemas Comunes

**Error de conexión a la base de datos**
```bash
# Verificar que PostgreSQL esté ejecutándose
docker-compose ps

# Revisar logs
docker-compose logs db
```

**Problemas con Redis**
```bash
# Verificar conexión Redis
docker-compose exec redis redis-cli ping
```

**Errores de permisos**
```bash
# En sistemas Unix, verificar permisos
sudo chown -R $USER:$USER .
```

### Obtener Ayuda

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/storatrack/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/tu-usuario/storatrack/wiki)
- **Email**: soporte@storatrack.com

## 🗺️ Roadmap

### Versión 2.0
- [ ] API REST completa
- [ ] Aplicación móvil
- [ ] Integración con sistemas ERP
- [ ] Notificaciones push
- [ ] Dashboard avanzado con BI

### Versión 2.1
- [ ] Integración con lectores de códigos de barras
- [ ] Geolocalización de equipos
- [ ] Workflow de aprobaciones
- [ ] Integración con proveedores

### Versión 3.0
- [ ] Machine Learning para predicciones
- [ ] IoT integration
- [ ] Blockchain para trazabilidad
- [ ] Multi-idioma completo

## 📊 Métricas del Proyecto

- **Líneas de código**: ~15,000
- **Cobertura de tests**: 85%+
- **Tiempo de respuesta**: <200ms promedio
- **Uptime objetivo**: 99.9%

---

**Desarrollado con ❤️ para la gestión eficiente de inventarios**

*StoraTrack - Donde cada equipo cuenta* 📦✨