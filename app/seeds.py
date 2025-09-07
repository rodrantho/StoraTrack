#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos iniciales (seeds)
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models import (
    Base, User, Company, Location, Device, Tag, DeviceTag,
    DeviceMovement, UserRole, DeviceStatus, DeviceCondition
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_tables():
    """Crear todas las tablas"""
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas")

def seed_companies(db: Session):
    """Crear empresas de ejemplo"""
    print("Creando empresas...")
    
    companies = [
        {
            "name": "TechCorp S.A.",
            "rut_id": "76.123.456-7",
            "contact_name": "Juan Pérez",
            "email": "contacto@techcorp.cl",
            "phone": "+56 2 2345 6789",
            "address": "Av. Providencia 1234, Santiago",
            "costo_base_default": 5000.0,
            "costo_diario_default": 1500.0
        },
        {
            "name": "Innovación Digital Ltda.",
            "rut_id": "77.987.654-3",
            "contact_name": "María González",
            "email": "info@innovacion.cl",
            "phone": "+56 2 9876 5432",
            "address": "Las Condes 5678, Santiago",
            "costo_base_default": 3000.0,
            "costo_diario_default": 1000.0
        },
        {
            "name": "Soluciones Empresariales SpA",
            "rut_id": "78.555.444-9",
            "contact_name": "Carlos Rodríguez",
            "email": "ventas@soluciones.cl",
            "phone": "+56 2 5555 4444",
            "address": "Vitacura 9999, Santiago",
            "costo_base_default": 4000.0,
            "costo_diario_default": 1200.0
        }
    ]
    
    created_companies = []
    for company_data in companies:
        # Verificar si ya existe
        existing = db.query(Company).filter(Company.rut_id == company_data["rut_id"]).first()
        if not existing:
            company = Company(**company_data)
            db.add(company)
            db.flush()  # Para obtener el ID
            created_companies.append(company)
            print(f"  ✓ Empresa creada: {company.name}")
        else:
            created_companies.append(existing)
            print(f"  - Empresa ya existe: {existing.name}")
    
    db.commit()
    return created_companies

def seed_users(db: Session, companies: list):
    """Crear usuarios de ejemplo"""
    print("Creando usuarios...")
    
    users = [
        # NOTA: Cambiar estas credenciales en producción
        {
            "email": "admin@storatrack.com",
            "password": "change_me_admin_2024",
            "full_name": "Administrador Principal",
            "role": UserRole.superadmin,
            "company_id": None
        },
        {
            "email": "staff@storatrack.com",
            "password": "change_me_staff_2024",
            "full_name": "Personal de Staff",
            "role": UserRole.staff,
            "company_id": None
        },
        {
            "email": "cliente1@techcorp.cl",
            "password": "change_me_client_2024",
            "full_name": "Usuario TechCorp",
            "role": UserRole.client,
            "company_id": companies[0].id if companies else None
        },
        {
            "email": "cliente2@innovacion.cl",
            "password": "change_me_client_2024",
            "full_name": "Usuario Innovación",
            "role": UserRole.client,
            "company_id": companies[1].id if len(companies) > 1 else None
        },
        {
            "email": "cliente3@soluciones.cl",
            "password": "change_me_client_2024",
            "full_name": "Usuario Soluciones",
            "role": UserRole.client,
            "company_id": companies[2].id if len(companies) > 2 else None
        }
    ]
    
    created_users = []
    for user_data in users:
        # Verificar si ya existe
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
            user = User(**user_data)
            db.add(user)
            db.flush()
            created_users.append(user)
            print(f"  ✓ Usuario creado: {user.email} ({user.role.value})")
        else:
            created_users.append(existing)
            print(f"  - Usuario ya existe: {existing.email}")
    
    db.commit()
    return created_users

def seed_locations(db: Session, companies: list):
    """Crear ubicaciones de ejemplo"""
    print("Creando ubicaciones...")
    
    locations_data = [
        # TechCorp
        {
            "name": "Bodega Principal",
            "code": "TC-BP-001",
            "description": "Bodega principal de TechCorp",
            "company_id": companies[0].id,
            "max_capacity": 100,
            "sort_order": 1
        },
        {
            "name": "Sala de Servidores",
            "code": "TC-SS-001",
            "description": "Sala de servidores climatizada",
            "company_id": companies[0].id,
            "max_capacity": 50,
            "sort_order": 2
        },
        # Innovación Digital
        {
            "name": "Almacén Norte",
            "code": "ID-AN-001",
            "description": "Almacén ubicado en el norte",
            "company_id": companies[1].id if len(companies) > 1 else companies[0].id,
            "max_capacity": 75,
            "sort_order": 1
        },
        {
            "name": "Oficina Central",
            "code": "ID-OC-001",
            "description": "Oficina central para equipos temporales",
            "company_id": companies[1].id if len(companies) > 1 else companies[0].id,
            "max_capacity": 25,
            "sort_order": 2
        },
        # Soluciones Empresariales
        {
            "name": "Depósito Sur",
            "code": "SE-DS-001",
            "description": "Depósito principal en el sur",
            "company_id": companies[2].id if len(companies) > 2 else companies[0].id,
            "max_capacity": 120,
            "sort_order": 1
        }
    ]
    
    created_locations = []
    for location_data in locations_data:
        # Verificar si ya existe
        existing = db.query(Location).filter(
            Location.code == location_data["code"],
            Location.company_id == location_data["company_id"]
        ).first()
        
        if not existing:
            location = Location(**location_data)
            db.add(location)
            db.flush()
            created_locations.append(location)
            print(f"  ✓ Ubicación creada: {location.name} ({location.code})")
        else:
            created_locations.append(existing)
            print(f"  - Ubicación ya existe: {existing.name}")
    
    db.commit()
    return created_locations

def seed_tags(db: Session, companies: list):
    """Crear tags de ejemplo"""
    print("Creando tags...")
    
    tags_data = [
        # Tags generales
        {"name": "Laptop", "color": "#007bff", "description": "Computadores portátiles", "company_id": None},
        {"name": "Desktop", "color": "#28a745", "description": "Computadores de escritorio", "company_id": None},
        {"name": "Monitor", "color": "#ffc107", "description": "Monitores y pantallas", "company_id": None},
        {"name": "Servidor", "color": "#dc3545", "description": "Servidores", "company_id": None},
        {"name": "Red", "color": "#6f42c1", "description": "Equipos de red", "company_id": None},
        
        # Tags específicos por empresa
        {"name": "Crítico", "color": "#fd7e14", "description": "Equipos críticos", "company_id": companies[0].id},
        {"name": "Desarrollo", "color": "#20c997", "description": "Equipos de desarrollo", "company_id": companies[1].id if len(companies) > 1 else companies[0].id},
        {"name": "Producción", "color": "#e83e8c", "description": "Equipos de producción", "company_id": companies[2].id if len(companies) > 2 else companies[0].id},
    ]
    
    created_tags = []
    for tag_data in tags_data:
        # Verificar si ya existe
        existing = db.query(Tag).filter(
            Tag.name == tag_data["name"],
            Tag.company_id == tag_data["company_id"]
        ).first()
        
        if not existing:
            tag = Tag(**tag_data)
            db.add(tag)
            db.flush()
            created_tags.append(tag)
            print(f"  ✓ Tag creado: {tag.name}")
        else:
            created_tags.append(existing)
            print(f"  - Tag ya existe: {existing.name}")
    
    db.commit()
    return created_tags

def seed_devices(db: Session, companies: list, locations: list, tags: list):
    """Crear dispositivos de ejemplo"""
    print("Creando dispositivos...")
    
    devices_data = [
        # TechCorp devices
        {
            "name": "Laptop Dell Latitude 7420",
            "serial_number": "DL7420001",
            "brand": "Dell",
            "model": "Latitude 7420",
            "condition": DeviceCondition.excellent,
            "status": DeviceStatus.stored,
            "description": "Laptop ejecutivo con Windows 11 Pro",
            "company_id": companies[0].id,
            "location_id": locations[0].id if locations else None,
            "costo_base": 5000.0,
            "costo_diario": 1500.0,
            "entry_date": datetime.now() - timedelta(days=15)
        },
        {
            "name": "Monitor Samsung 27\" 4K",
            "serial_number": "SM27001",
            "brand": "Samsung",
            "model": "U28E590D",
            "condition": DeviceCondition.good,
            "status": DeviceStatus.stored,
            "description": "Monitor 4K para diseño gráfico",
            "company_id": companies[0].id,
            "location_id": locations[0].id if locations else None,
            "costo_base": 3000.0,
            "costo_diario": 800.0,
            "entry_date": datetime.now() - timedelta(days=10)
        },
        {
            "name": "Servidor HP ProLiant DL380",
            "serial_number": "HP380001",
            "brand": "HP",
            "model": "ProLiant DL380 Gen10",
            "condition": DeviceCondition.excellent,
            "status": DeviceStatus.in_process,
            "description": "Servidor para aplicaciones críticas",
            "company_id": companies[0].id,
            "location_id": locations[1].id if len(locations) > 1 else locations[0].id,
            "costo_base": 15000.0,
            "costo_diario": 3000.0,
            "entry_date": datetime.now() - timedelta(days=5)
        },
        
        # Innovación Digital devices
        {
            "name": "MacBook Pro 16\" M2",
            "serial_number": "MBP16001",
            "brand": "Apple",
            "model": "MacBook Pro 16\"",
            "condition": DeviceCondition.excellent,
            "status": DeviceStatus.stored,
            "description": "MacBook Pro para desarrollo",
            "company_id": companies[1].id if len(companies) > 1 else companies[0].id,
            "location_id": locations[2].id if len(locations) > 2 else locations[0].id,
            "costo_base": 8000.0,
            "costo_diario": 2000.0,
            "entry_date": datetime.now() - timedelta(days=20)
        },
        {
            "name": "Switch Cisco Catalyst 2960",
            "serial_number": "CS2960001",
            "brand": "Cisco",
            "model": "Catalyst 2960-X",
            "condition": DeviceCondition.good,
            "status": DeviceStatus.finished,
            "description": "Switch de red 24 puertos",
            "company_id": companies[1].id if len(companies) > 1 else companies[0].id,
            "location_id": locations[3].id if len(locations) > 3 else locations[0].id,
            "costo_base": 4000.0,
            "costo_diario": 1000.0,
            "entry_date": datetime.now() - timedelta(days=30),
            "exit_date": datetime.now() - timedelta(days=2)
        }
    ]
    
    created_devices = []
    for device_data in devices_data:
        # Verificar si ya existe
        existing = db.query(Device).filter(
            Device.serial_number == device_data["serial_number"]
        ).first()
        
        if not existing:
            device = Device(**device_data)
            db.add(device)
            db.flush()
            created_devices.append(device)
            print(f"  ✓ Dispositivo creado: {device.name} ({device.serial_number})")
        else:
            created_devices.append(existing)
            print(f"  - Dispositivo ya existe: {existing.name}")
    
    db.commit()
    return created_devices

def seed_device_tags(db: Session, devices: list, tags: list):
    """Asignar tags a dispositivos"""
    print("Asignando tags a dispositivos...")
    
    # Mapeo de dispositivos a tags
    device_tag_mapping = [
        (0, [0, 5]),  # Laptop Dell -> Laptop, Crítico
        (1, [2]),     # Monitor Samsung -> Monitor
        (2, [3, 5]),  # Servidor HP -> Servidor, Crítico
        (3, [0, 6]),  # MacBook Pro -> Laptop, Desarrollo
        (4, [4]),     # Switch Cisco -> Red
    ]
    
    for device_idx, tag_indices in device_tag_mapping:
        if device_idx < len(devices):
            device = devices[device_idx]
            for tag_idx in tag_indices:
                if tag_idx < len(tags):
                    tag = tags[tag_idx]
                    
                    # Verificar si ya existe la relación
                    existing = db.query(DeviceTag).filter(
                        DeviceTag.device_id == device.id,
                        DeviceTag.tag_id == tag.id
                    ).first()
                    
                    if not existing:
                        device_tag = DeviceTag(device_id=device.id, tag_id=tag.id)
                        db.add(device_tag)
                        print(f"  ✓ Tag '{tag.name}' asignado a '{device.name}'")
    
    db.commit()

def seed_device_movements(db: Session, devices: list, locations: list):
    """Crear movimientos de dispositivos"""
    print("Creando movimientos de dispositivos...")
    
    movements_data = [
        {
            "device_id": devices[0].id,
            "from_status": None,
            "to_status": DeviceStatus.stored,
            "from_location_id": None,
            "to_location_id": locations[0].id if locations else None,
            "notes": "Ingreso inicial del dispositivo",
            "movement_date": devices[0].entry_date
        },
        {
            "device_id": devices[2].id,
            "from_status": DeviceStatus.stored,
            "to_status": DeviceStatus.in_process,
            "from_location_id": locations[0].id if locations else None,
            "to_location_id": locations[1].id if len(locations) > 1 else None,
            "notes": "Movido a sala de servidores para configuración",
            "movement_date": datetime.now() - timedelta(days=3)
        },
        {
            "device_id": devices[4].id if len(devices) > 4 else devices[0].id,
            "from_status": DeviceStatus.stored,
            "to_status": DeviceStatus.finished,
            "from_location_id": locations[3].id if len(locations) > 3 else locations[0].id,
            "to_location_id": None,
            "notes": "Dispositivo entregado al cliente",
            "movement_date": datetime.now() - timedelta(days=2)
        }
    ]
    
    for movement_data in movements_data:
        movement = DeviceMovement(**movement_data)
        db.add(movement)
        print(f"  ✓ Movimiento creado para dispositivo ID {movement.device_id}")
    
    db.commit()

def main():
    """Función principal para ejecutar todos los seeds"""
    print("🌱 Iniciando proceso de seeds...")
    
    # Crear tablas
    create_tables()
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # Ejecutar seeds en orden
        companies = seed_companies(db)
        users = seed_users(db, companies)
        locations = seed_locations(db, companies)
        tags = seed_tags(db, companies)
        devices = seed_devices(db, companies, locations, tags)
        seed_device_tags(db, devices, tags)
        seed_device_movements(db, devices, locations)
        
        print("\n✅ Seeds completados exitosamente!")
        print(f"\n📊 Resumen:")
        print(f"  - {len(companies)} empresas")
        print(f"  - {len(users)} usuarios")
        print(f"  - {len(locations)} ubicaciones")
        print(f"  - {len(tags)} tags")
        print(f"  - {len(devices)} dispositivos")
        
        print("\n🔑 Credenciales de acceso:")
        print("  Superadmin: admin@storatrack.com / admin123")
        print("  Staff: staff@storatrack.com / staff123")
        print("  Cliente 1: cliente1@techcorp.cl / cliente123")
        print("  Cliente 2: cliente2@innovacion.cl / cliente123")
        print("  Cliente 3: cliente3@soluciones.cl / cliente123")
        
    except Exception as e:
        print(f"❌ Error ejecutando seeds: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()