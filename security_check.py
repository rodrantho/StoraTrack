#!/usr/bin/env python3
"""Script de verificación de seguridad para StoraTrack"""

import os
import sys
from pathlib import Path
from production_config import validate_production_config, PRODUCTION_CHECKLIST

def check_file_permissions():
    """Verifica permisos de archivos sensibles"""
    issues = []
    
    # Archivos que deben tener permisos restrictivos
    sensitive_files = [
        ".env",
        "database/storatrack.db",
        "app/config.py"
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            # En Windows, verificamos que el archivo no sea de solo lectura para todos
            stat_info = os.stat(file_path)
            if stat_info.st_mode & 0o077:  # Otros usuarios tienen permisos
                issues.append(f"Archivo {file_path} tiene permisos demasiado amplios")
    
    return issues

def check_default_credentials():
    """Verifica credenciales por defecto"""
    issues = []
    
    # Verificar archivo .env
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read().lower()
            
        if "change" in content or "default" in content or "example" in content:
            issues.append("Archivo .env contiene valores por defecto")
    
    return issues

def check_debug_settings():
    """Verifica que debug esté desactivado"""
    issues = []
    
    # Verificar main.py
    if os.path.exists("main.py"):
        with open("main.py", "r") as f:
            content = f.read()
            
        if "reload=True" in content:
            issues.append("Reload está activado en main.py (debe ser False para producción)")
        
        if "debug=True" in content.lower():
            issues.append("Debug está activado (debe ser False para producción)")
    
    return issues

def check_database_config():
    """Verifica configuración de base de datos"""
    issues = []
    
    db_url = os.getenv("DATABASE_URL", "")
    
    if "sqlite" in db_url.lower():
        issues.append("Se está usando SQLite (recomendado: PostgreSQL para producción)")
    
    if not db_url or "localhost" in db_url:
        issues.append("Base de datos configurada en localhost (verificar para producción)")
    
    return issues

def check_cors_settings():
    """Verifica configuración de CORS"""
    issues = []
    
    # Verificar main.py para configuración de CORS
    if os.path.exists("main.py"):
        with open("main.py", "r") as f:
            content = f.read()
            
        if 'allow_origins=["*"]' in content:
            issues.append("CORS configurado para permitir todos los orígenes (inseguro)")
        
        if 'allowed_hosts=["*"]' in content:
            issues.append("TrustedHostMiddleware configurado para permitir todos los hosts (inseguro)")
    
    return issues

def check_static_files():
    """Verifica configuración de archivos estáticos"""
    issues = []
    
    # Verificar que existan directorios necesarios
    required_dirs = ["static", "static/css", "static/js", "static/images"]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            issues.append(f"Directorio {dir_path} no existe")
    
    return issues

def run_security_audit():
    """Ejecuta auditoría completa de seguridad"""
    print("🔒 AUDITORÍA DE SEGURIDAD - StoraTrack")
    print("=" * 50)
    
    all_issues = []
    
    # Verificaciones de configuración
    print("\n📋 Verificando configuración de producción...")
    config_issues = validate_production_config()
    if config_issues:
        all_issues.extend(config_issues)
        for issue in config_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ Configuración de producción válida")
    
    # Verificaciones de permisos
    print("\n🔐 Verificando permisos de archivos...")
    perm_issues = check_file_permissions()
    if perm_issues:
        all_issues.extend(perm_issues)
        for issue in perm_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ Permisos de archivos correctos")
    
    # Verificaciones de credenciales
    print("\n🔑 Verificando credenciales por defecto...")
    cred_issues = check_default_credentials()
    if cred_issues:
        all_issues.extend(cred_issues)
        for issue in cred_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ No se encontraron credenciales por defecto")
    
    # Verificaciones de debug
    print("\n🐛 Verificando configuración de debug...")
    debug_issues = check_debug_settings()
    if debug_issues:
        all_issues.extend(debug_issues)
        for issue in debug_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ Configuración de debug correcta")
    
    # Verificaciones de base de datos
    print("\n🗄️ Verificando configuración de base de datos...")
    db_issues = check_database_config()
    if db_issues:
        all_issues.extend(db_issues)
        for issue in db_issues:
            print(f"  ⚠️ {issue}")
    else:
        print("  ✅ Configuración de base de datos correcta")
    
    # Verificaciones de CORS
    print("\n🌐 Verificando configuración de CORS...")
    cors_issues = check_cors_settings()
    if cors_issues:
        all_issues.extend(cors_issues)
        for issue in cors_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ Configuración de CORS segura")
    
    # Verificaciones de archivos estáticos
    print("\n📁 Verificando archivos estáticos...")
    static_issues = check_static_files()
    if static_issues:
        all_issues.extend(static_issues)
        for issue in static_issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ Archivos estáticos configurados correctamente")
    
    # Resumen
    print("\n" + "=" * 50)
    if all_issues:
        print(f"❌ AUDITORÍA FALLIDA: {len(all_issues)} problemas encontrados")
        print("\n🔧 PROBLEMAS A RESOLVER:")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print("✅ AUDITORÍA EXITOSA: No se encontraron problemas de seguridad")
        return True

def show_production_checklist():
    """Muestra lista de verificación para producción"""
    print("\n📋 LISTA DE VERIFICACIÓN PARA PRODUCCIÓN")
    print("=" * 50)
    for item in PRODUCTION_CHECKLIST:
        print(f"  {item}")
    print("\n💡 Asegúrate de completar todos los elementos antes del despliegue.")

if __name__ == "__main__":
    print("StoraTrack - Script de Verificación de Seguridad")
    print("Versión 1.0.0\n")
    
    # Ejecutar auditoría
    audit_passed = run_security_audit()
    
    # Mostrar checklist
    show_production_checklist()
    
    # Código de salida
    if not audit_passed:
        print("\n⚠️ ATENCIÓN: Resuelve los problemas antes del despliegue en producción.")
        sys.exit(1)
    else:
        print("\n🎉 ¡La aplicación está lista para producción!")
        sys.exit(0)