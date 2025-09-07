#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de la base de datos
"""

import sys
import os
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import (
    User, Company, Location, Device, Tag,
    DeviceMovement, UserRole, CostCalculation, MonthlyReport, AuditLog
)

def clean_test_data():
    """Eliminar datos de prueba de la base de datos"""
    db = SessionLocal()
    
    try:
        print("Iniciando limpieza de datos de prueba...")
        
        # Eliminar reportes mensuales
        reports_count = db.query(MonthlyReport).count()
        if reports_count > 0:
            db.query(MonthlyReport).delete()
            print(f"✓ Eliminados {reports_count} reportes mensuales")
        
        # Eliminar cálculos de costos
        costs_count = db.query(CostCalculation).count()
        if costs_count > 0:
            db.query(CostCalculation).delete()
            print(f"✓ Eliminados {costs_count} cálculos de costos")
        
        # Eliminar movimientos de dispositivos
        movements_count = db.query(DeviceMovement).count()
        if movements_count > 0:
            db.query(DeviceMovement).delete()
            print(f"✓ Eliminados {movements_count} movimientos de dispositivos")
        
        # Eliminar dispositivos
        devices_count = db.query(Device).count()
        if devices_count > 0:
            db.query(Device).delete()
            print(f"✓ Eliminados {devices_count} dispositivos")
        
        # Eliminar tags
        tags_count = db.query(Tag).count()
        if tags_count > 0:
            db.query(Tag).delete()
            print(f"✓ Eliminados {tags_count} tags")
        
        # Eliminar ubicaciones
        locations_count = db.query(Location).count()
        if locations_count > 0:
            db.query(Location).delete()
            print(f"✓ Eliminadas {locations_count} ubicaciones")
        
        # Eliminar usuarios de prueba (mantener solo admin principal)
        test_users = db.query(User).filter(
            User.email.in_([
                'staff@storatrack.com',
                'cliente1@techcorp.cl',
                'cliente2@innovacion.cl',
                'cliente3@soluciones.cl'
            ])
        ).all()
        
        for user in test_users:
            db.delete(user)
            print(f"✓ Usuario eliminado: {user.email}")
        
        # Eliminar empresas de prueba
        test_companies = db.query(Company).filter(
            Company.rut_id.in_([
                '76.123.456-7',
                '77.987.654-3',
                '78.555.444-9'
            ])
        ).all()
        
        for company in test_companies:
            db.delete(company)
            print(f"✓ Empresa eliminada: {company.name}")
        
        # Actualizar el usuario admin para producción
        admin_user = db.query(User).filter(
            User.email == 'admin@storatrack.com'
        ).first()
        
        if admin_user:
            # Cambiar email a uno más genérico para producción
            admin_user.email = 'admin@localhost'
            admin_user.full_name = 'Administrador'
            print("✓ Usuario admin actualizado para producción")
        
        db.commit()
        print("\n🎉 Limpieza completada exitosamente!")
        print("\n⚠️  IMPORTANTE: Cambia la contraseña del usuario admin antes de ir a producción")
        print("   Email: admin@localhost")
        print("   Contraseña temporal: change_me_admin_2024")
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clean_test_data()