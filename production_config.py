"""Configuración específica para producción de StoraTrack"""

import os
from app.config import Settings

class ProductionSettings(Settings):
    """Configuración optimizada para producción"""
    
    # Seguridad mejorada
    secret_key: str = os.getenv("SECRET_KEY")
    
    # Configuración de CORS más restrictiva
    cors_origins: list = [
        "https://tu-dominio.com",
        "https://www.tu-dominio.com"
    ]
    
    # Hosts permitidos
    allowed_hosts: list = [
        "tu-dominio.com",
        "www.tu-dominio.com",
        "localhost"  # Solo para testing local
    ]
    
    # Base de datos para producción
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/storatrack")
    
    # Configuración de logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Desactivar debug en producción
    debug: bool = False
    
    # Configuración de SSL
    ssl_enabled: bool = os.getenv("SSL_ENABLED", "false").lower() == "true"
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Configuración de archivos
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # Configuración de sesiones
    session_timeout: int = 3600  # 1 hora
    
    # Configuración de backup
    backup_enabled: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Función para validar configuración de producción
def validate_production_config():
    """Valida que la configuración de producción sea segura"""
    errors = []
    
    # Verificar SECRET_KEY
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key or len(secret_key) < 32:
        errors.append("SECRET_KEY debe tener al menos 32 caracteres")
    
    if secret_key and "change" in secret_key.lower():
        errors.append("SECRET_KEY contiene texto por defecto, debe ser cambiada")
    
    # Verificar base de datos
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "sqlite" in db_url:
        errors.append("Se recomienda usar PostgreSQL o MySQL para producción")
    
    # Verificar configuración de hosts
    allowed_hosts = os.getenv("ALLOWED_HOSTS")
    if not allowed_hosts or "*" in allowed_hosts:
        errors.append("ALLOWED_HOSTS debe especificar dominios específicos")
    
    return errors

# Lista de verificación para producción
PRODUCTION_CHECKLIST = [
    "✓ Cambiar SECRET_KEY por una clave segura",
    "✓ Configurar base de datos PostgreSQL/MySQL",
    "✓ Configurar ALLOWED_HOSTS con dominios específicos",
    "✓ Configurar CORS_ORIGINS con dominios específicos",
    "✓ Activar SSL (HTTPS)",
    "✓ Configurar backup automático",
    "✓ Configurar monitoreo de logs",
    "✓ Cambiar contraseña del usuario admin",
    "✓ Configurar servidor web (Nginx/Apache)",
    "✓ Configurar firewall",
    "✓ Configurar certificados SSL",
    "✓ Probar todas las funcionalidades"
]