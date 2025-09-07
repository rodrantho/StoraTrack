#!/usr/bin/env python3
"""
Script para crear datos de prueba en StoraTrack
Usa la API directamente para crear usuarios, empresas, ubicaciones y dispositivos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import User, Company, Location, Device, UserRole, DeviceStatus, LocationType
from app.auth import get_password_hash
from app.utils.datetime_utils import now_local
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def create_test_data():
    """Crear todos los datos de prueba"""
    print("=== CREANDO DATOS DE PRUEBA STORATRACK ===")
    
    # Obtener sesión de base de datos
    db = next(get_db())
    
    try:
        # 1. Crear usuario staff de prueba
        print("\n1. Creando usuario staff de prueba...")
        staff_user = create_staff_user(db)
        
        # 2. Crear empresa de prueba
        print("\n2. Creando empresa de prueba...")
        test_company = create_test_company(db)
        
        # 3. Crear ubicaciones de prueba
        print("\n3. Creando ubicaciones de prueba...")
        locations = create_test_locations(db, test_company)
        
        # 4. Crear dispositivos de prueba
        print("\n4. Creando dispositivos de prueba...")
        devices = create_test_devices(db, test_company, locations)
        
        # 5. Crear usuarios cliente de prueba
        print("\n5. Creando usuarios cliente de prueba...")
        client_users = create_client_users(db, test_company)
        
        print("\n=== DATOS DE PRUEBA CREADOS EXITOSAMENTE ===")
        print(f"✓ Usuario staff: {staff_user.email}")
        print(f"✓ Empresa: {test_company.name}")
        print(f"✓ Ubicaciones: {len(locations)} creadas")
        print(f"✓ Dispositivos: {len(devices)} creados")
        print(f"✓ Usuarios cliente: {len(client_users)} creados")
        
        print("\n=== CREDENCIALES DE PRUEBA ===")
        print(f"Staff: {staff_user.email} / test123456")
        for user in client_users:
            print(f"Cliente: {user.email} / test123456")
            
        print("\n=== URLS DE PRUEBA ===")
        print("Admin Dashboard: http://localhost:4011/admin/dashboard")
        print("Usuarios: http://localhost:4011/admin/users")
        print("Empresas: http://localhost:4011/admin/companies")
        print("Ubicaciones: http://localhost:4011/admin/locations")
        print("Dispositivos: http://localhost:4011/admin/devices")
        print("Cliente Dashboard: http://localhost:4011/client/dashboard")
        
    except Exception as e:
        print(f"Error creando datos de prueba: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_staff_user(db: Session):
    """Crear usuario staff de prueba"""
    # Verificar si ya existe
    existing = db.query(User).filter(User.email == "staff_test@storatrack.com").first()
    if existing:
        print("  - Usuario staff ya existe")
        return existing
    
    user = User(
        email="staff_test@storatrack.com",
        hashed_password=get_password_hash("test123456"),
        full_name="Staff de Prueba",
        role=UserRole.STAFF,
        company_id=None,
        is_active=True,
        created_at=now_local()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"  ✓ Usuario staff creado: {user.email}")
    return user

def create_test_company(db: Session):
    """Crear empresa de prueba"""
    # Verificar si ya existe
    existing = db.query(Company).filter(Company.name == "Empresa Test CRUD").first()
    if existing:
        print("  - Empresa de prueba ya existe")
        return existing
    
    company = Company(
        name="Empresa Test CRUD",
        rut_id="12345678-9",
        contact_name="Contacto de Prueba",
        email="test@empresatest.com",
        phone="+56912345678",
        address="Dirección de Prueba 123, Santiago",
        costo_base_default=1000.0,
        costo_diario_default=50.0,
        iva_percent=19.0,
        incluir_iva=True,
        currency="CLP",
        timezone="America/Santiago",
        is_active=True,
        created_at=now_local()
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"  ✓ Empresa creada: {company.name}")
    return company

def create_test_locations(db: Session, company: Company):
    """Crear ubicaciones de prueba"""
    locations = []
    
    # Ubicación principal (bodega)
    main_location_data = {
        "name": "Bodega Principal Test",
        "code": "BPT001",
        "description": "Bodega principal para testing CRUD",
        "location_type": LocationType.DEPOSITO,
        "company_id": company.id,
        "parent_id": None,
        "sort_order": 1,
        "max_capacity": 1000,
        "shelf_count": 10,
        "is_active": True,
        "created_at": now_local()
    }
    
    # Verificar si ya existe
    existing = db.query(Location).filter(Location.code == "BPT001").first()
    if not existing:
        main_location = Location(**main_location_data)
        db.add(main_location)
        db.commit()
        db.refresh(main_location)
        locations.append(main_location)
        print(f"  ✓ Ubicación principal creada: {main_location.name}")
    else:
        main_location = existing
        locations.append(main_location)
        print(f"  - Ubicación principal ya existe: {main_location.name}")
    
    # Sub-ubicaciones (estantes)
    sub_locations_data = [
        {
            "name": "Estante A1 Test",
            "code": "EA1T001",
            "description": "Estante A1 para testing",
            "location_type": LocationType.ESTANTE,
            "company_id": company.id,
            "parent_id": main_location.id,
            "sort_order": 1,
            "max_capacity": 50,
            "shelf_count": 1,
            "is_active": True,
            "created_at": now_local()
        },
        {
            "name": "Estante B2 Test",
            "code": "EB2T001",
            "description": "Estante B2 para testing",
            "location_type": LocationType.ESTANTE,
            "company_id": company.id,
            "parent_id": main_location.id,
            "sort_order": 2,
            "max_capacity": 30,
            "shelf_count": 1,
            "is_active": True,
            "created_at": now_local()
        }
    ]
    
    for sub_data in sub_locations_data:
        existing = db.query(Location).filter(Location.code == sub_data["code"]).first()
        if not existing:
            sub_location = Location(**sub_data)
            db.add(sub_location)
            db.commit()
            db.refresh(sub_location)
            locations.append(sub_location)
            print(f"  ✓ Sub-ubicación creada: {sub_location.name}")
        else:
            locations.append(existing)
            print(f"  - Sub-ubicación ya existe: {existing.name}")
    
    return locations

def create_test_devices(db: Session, company: Company, locations: list):
    """Crear dispositivos de prueba"""
    devices = []
    
    devices_data = [
        {
            "name": "Laptop Test 001",
            "serial_number": "TEST001",
            "brand": "TestBrand",
            "model": "TestModel1",
            "company_id": company.id,
            "location_id": locations[0].id if locations else None,
            "status": DeviceStatus.ALMACENADO,
            "description": "Laptop de prueba para testing CRUD",
            "costo_base": 500000.0,
            "costo_diario": 1000.0,
            "is_active": True,
            "created_at": now_local()
        },
        {
            "name": "Desktop Test 002",
            "serial_number": "TEST002",
            "brand": "TestBrand",
            "model": "TestModel2",
            "company_id": company.id,
            "location_id": locations[1].id if len(locations) > 1 else locations[0].id,
            "status": DeviceStatus.INGRESADO,
            "description": "Desktop de prueba para testing CRUD",
            "costo_base": 800000.0,
            "costo_diario": 1500.0,
            "is_active": True,
            "created_at": now_local()
        },
        {
            "name": "Tablet Test 003",
            "serial_number": "TEST003",
            "brand": "TestBrand",
            "model": "TestModel3",
            "company_id": company.id,
            "location_id": locations[2].id if len(locations) > 2 else locations[0].id,
            "status": DeviceStatus.ESPERANDO_RECIBIR,
            "description": "Tablet de prueba para testing CRUD",
            "costo_base": 300000.0,
            "costo_diario": 800.0,
            "is_active": True,
            "created_at": now_local()
        }
    ]
    
    for device_data in devices_data:
        existing = db.query(Device).filter(Device.serial_number == device_data["serial_number"]).first()
        if not existing:
            device = Device(**device_data)
            db.add(device)
            db.commit()
            db.refresh(device)
            devices.append(device)
            print(f"  ✓ Dispositivo creado: {device.serial_number} ({device.name})")
        else:
            devices.append(existing)
            print(f"  - Dispositivo ya existe: {existing.serial_number}")
    
    return devices

def create_client_users(db: Session, company: Company):
    """Crear usuarios cliente de prueba"""
    users = []
    
    users_data = [
        {
            "email": "cliente1_test@storatrack.com",
            "hashed_password": get_password_hash("test123456"),
            "full_name": "Cliente Test 1",
            "role": UserRole.CLIENT_USER,
            "company_id": company.id,
            "is_active": True,
            "created_at": now_local()
        },
        {
            "email": "cliente2_test@storatrack.com",
            "hashed_password": get_password_hash("test123456"),
            "full_name": "Cliente Test 2",
            "role": UserRole.CLIENT_USER,
            "company_id": company.id,
            "is_active": True,
            "created_at": now_local()
        }
    ]
    
    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(**user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
            users.append(user)
            print(f"  ✓ Usuario cliente creado: {user.email}")
        else:
            users.append(existing)
            print(f"  - Usuario cliente ya existe: {existing.email}")
    
    return users

def cleanup_test_data():
    """Limpiar datos de prueba"""
    print("=== LIMPIANDO DATOS DE PRUEBA ===")
    
    db = next(get_db())
    
    try:
        # Eliminar dispositivos de prueba
        devices = db.query(Device).filter(Device.serial_number.like("TEST%")).all()
        for device in devices:
            db.delete(device)
            print(f"  ✓ Dispositivo eliminado: {device.serial_number}")
        
        # Eliminar ubicaciones de prueba
        locations = db.query(Location).filter(Location.code.like("%T001")).all()
        for location in locations:
            db.delete(location)
            print(f"  ✓ Ubicación eliminada: {location.name}")
        
        # Eliminar usuarios de prueba
        test_emails = ["staff_test@storatrack.com", "cliente1_test@storatrack.com", "cliente2_test@storatrack.com"]
        for email in test_emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.delete(user)
                print(f"  ✓ Usuario eliminado: {user.email}")
        
        # Eliminar empresa de prueba
        company = db.query(Company).filter(Company.name == "Empresa Test CRUD").first()
        if company:
            db.delete(company)
            print(f"  ✓ Empresa eliminada: {company.name}")
        
        db.commit()
        print("\n✅ Datos de prueba eliminados exitosamente")
        
    except Exception as e:
        print(f"Error limpiando datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestionar datos de prueba de StoraTrack")
    parser.add_argument("action", choices=["create", "cleanup"], help="Acción a realizar")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_test_data()
    elif args.action == "cleanup":
        cleanup_test_data()