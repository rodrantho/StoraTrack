# 🚀 Guía de Despliegue en Producción - StoraTrack

## 📋 Requisitos Previos

### Sistema Operativo
- Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- Python 3.8+
- PostgreSQL 12+ (recomendado) o MySQL 8.0+
- Nginx (recomendado) o Apache
- SSL/TLS certificado

### Hardware Mínimo
- CPU: 2 cores
- RAM: 4GB
- Almacenamiento: 20GB SSD
- Ancho de banda: 100 Mbps

## 🔧 Configuración Paso a Paso

### 1. Preparación del Servidor

```bash
# Actualizar sistema (Ubuntu/Debian)
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Crear usuario para la aplicación
sudo useradd -m -s /bin/bash storatrack
sudo usermod -aG sudo storatrack
```

### 2. Configuración de Base de Datos

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Crear base de datos y usuario
CREATE DATABASE storatrack;
CREATE USER storatrack_user WITH PASSWORD 'tu_contraseña_segura';
GRANT ALL PRIVILEGES ON DATABASE storatrack TO storatrack_user;
\q
```

### 3. Despliegue de la Aplicación

```bash
# Cambiar al usuario de la aplicación
sudo su - storatrack

# Clonar o copiar el código
git clone <tu-repositorio> /home/storatrack/storatrack
cd /home/storatrack/storatrack

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configuración de Variables de Entorno

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración
nano .env
```

**Configuración mínima requerida en `.env`:**

```env
# Seguridad
SECRET_KEY=tu-clave-super-secreta-de-al-menos-32-caracteres-aqui
ENVIRONMENT=production
DEBUG=false

# Base de datos
DATABASE_URL=postgresql://storatrack_user:tu_contraseña_segura@localhost:5432/storatrack

# Seguridad de red
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Configuración regional
TIMEZONE=America/Montevideo
CURRENCY=UYU
CURRENCY_SYMBOL=$
```

### 5. Inicialización de Base de Datos

```bash
# Ejecutar migraciones
python main.py  # Esto creará las tablas automáticamente

# Crear datos iniciales (opcional)
python app/seeds.py

# Limpiar datos de prueba (IMPORTANTE)
python clean_test_data.py
```

### 6. Verificación de Seguridad

```bash
# Ejecutar auditoría de seguridad
python security_check.py

# Resolver todos los problemas antes de continuar
```

### 7. Configuración de Nginx

Crear archivo `/etc/nginx/sites-available/storatrack`:

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:4011;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/storatrack/storatrack/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/storatrack /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Configuración de Systemd (Servicio)

Crear archivo `/etc/systemd/system/storatrack.service`:

```ini
[Unit]
Description=StoraTrack Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=storatrack
Group=storatrack
WorkingDirectory=/home/storatrack/storatrack
Environment=PATH=/home/storatrack/storatrack/venv/bin
ExecStart=/home/storatrack/storatrack/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable storatrack
sudo systemctl start storatrack
sudo systemctl status storatrack
```

## 🔒 Configuración de Seguridad Adicional

### Firewall

```bash
# Configurar UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Backup Automático

```bash
# Crear script de backup
sudo nano /home/storatrack/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/storatrack/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
pg_dump -h localhost -U storatrack_user storatrack > $BACKUP_DIR/db_backup_$DATE.sql

# Backup de archivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /home/storatrack/storatrack/static /home/storatrack/storatrack/uploads

# Limpiar backups antiguos (mantener 30 días)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

```bash
# Hacer ejecutable
chmod +x /home/storatrack/backup.sh

# Agregar a crontab
crontab -e
# Agregar línea: 0 2 * * * /home/storatrack/backup.sh
```

## 📊 Monitoreo y Logs

### Configuración de Logs

```bash
# Crear directorio de logs
sudo mkdir -p /var/log/storatrack
sudo chown storatrack:storatrack /var/log/storatrack

# Configurar logrotate
sudo nano /etc/logrotate.d/storatrack
```

```
/var/log/storatrack/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 storatrack storatrack
}
```

### Monitoreo de Salud

```bash
# Script de monitoreo
nano /home/storatrack/health_check.sh
```

```bash
#!/bin/bash
HEALTH_URL="https://tu-dominio.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "$(date): StoraTrack está funcionando correctamente"
else
    echo "$(date): ERROR - StoraTrack no responde (HTTP $RESPONSE)"
    # Aquí puedes agregar notificaciones por email/Slack
fi
```

## ✅ Lista de Verificación Final

- [ ] Base de datos configurada y funcionando
- [ ] Variables de entorno configuradas correctamente
- [ ] SECRET_KEY cambiada por una segura
- [ ] Auditoría de seguridad pasada
- [ ] Nginx configurado con SSL
- [ ] Servicio systemd funcionando
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Logs configurados
- [ ] Monitoreo de salud funcionando
- [ ] Contraseña del admin cambiada
- [ ] Datos de prueba eliminados
- [ ] Todas las funcionalidades probadas

## 🆘 Solución de Problemas

### Logs del Sistema

```bash
# Ver logs de la aplicación
sudo journalctl -u storatrack -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Ver logs de PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Comandos Útiles

```bash
# Reiniciar servicios
sudo systemctl restart storatrack
sudo systemctl restart nginx
sudo systemctl restart postgresql

# Verificar estado
sudo systemctl status storatrack
sudo systemctl status nginx
sudo systemctl status postgresql

# Verificar puertos
sudo netstat -tlnp | grep :4011
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

## 📞 Soporte

Para soporte técnico o problemas de despliegue, consulta:
- Logs del sistema
- Documentación de la aplicación
- Ejecuta `python security_check.py` para verificar configuración

---

**⚠️ IMPORTANTE:** Siempre realiza pruebas en un entorno de staging antes de desplegar en producción.