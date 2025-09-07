from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import engine, SessionLocal
from app.models import (
    Base, User, Company, Location, Tag, Device, DeviceMovement,
    UserRole, DeviceStatus, DeviceCondition
)
from app.auth import get_password_hash
from app.config import settings
from app.utils.datetime_utils import now_local
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Crear todas las tablas en la base de datos"""
    logger.info("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas exitosamente")

def create_superadmin(db: Session):
    """Crear usuario superadmin por defecto"""
    logger.info("Creando usuario superadmin...")
    
    # Verificar si ya existe
    existing_admin = db.query(User).filter(
        User.email == "rodrantho@outlook.com"
    ).first()
    
    if existing_admin:
        logger.info("Usuario superadmin ya existe")
        return existing_admin
    
    admin_user = User(
        email="rodrantho@outlook.com",
        hashed_password=get_password_hash("Kernel1.0"),
        full_name="Rodrigo Anthonisen",
        role=UserRole.SUPERADMIN,
        is_active=True,
        created_at=now_local()
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    logger.info(f"Usuario superadmin creado: {admin_user.email}")
    return admin_user

def create_demo_company(db: Session):
    """Crear empresa demo"""
    logger.info("Creando empresa demo...")
    
    # Verificar si ya existe
    existing_company = db.query(Company).filter(
        Company.rut_id == "210001230017"
    ).first()
    
    if existing_company:
        logger.info("Empresa demo ya existe")
        return existing_company
    
    demo_company = Company(
        name="Empresa Demo S.A.",
        rut_id="210001230017",
        contact_name="Juan Pérez",
        email="contacto@empresademo.com",
        phone="+598 2123 4567",
        address="Av. 18 de Julio 1234, Montevideo, Uruguay",
        costo_base_default=500.00,
        costo_diario_default=25.00,
        iva_percent=22.0,
        incluir_iva=True,
        currency="UYU",
        timezone="America/Montevideo",
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(demo_company)
    db.commit()
    db.refresh(demo_company)
    
    logger.info(f"Empresa demo creada: {demo_company.name}")
    return demo_company

def create_demo_users(db: Session, company: Company):
    """Crear usuarios demo"""
    logger.info("Creando usuarios demo...")
    
    users_data = [
        {
            "email": "staff@demo.com",
            "password": "staff123",
            "full_name": "María García",
            "role": UserRole.STAFF,
            "company_id": None  # Staff puede acceder a todas las empresas
        },
        {
            "email": "cliente@demo.com",
            "password": "cliente123",
            "full_name": "Carlos Rodríguez",
            "role": UserRole.CLIENT_USER,
            "company_id": company.id
        }
    ]
    
    created_users = []
    
    for user_data in users_data:
        # Verificar si ya existe
        existing_user = db.query(User).filter(
            User.email == user_data["email"]
        ).first()
        
        if existing_user:
            logger.info(f"Usuario {user_data['email']} ya existe")
            created_users.append(existing_user)
            continue
        
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            company_id=user_data["company_id"],
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        created_users.append(user)
        logger.info(f"Usuario creado: {user.email} ({user.role.value})")
    
    return created_users

def create_demo_locations(db: Session, company: Company):
    """Crear ubicaciones demo"""
    logger.info("Creando ubicaciones demo...")
    
    locations_data = [
        {
            "name": "Depósito Principal",
            "description": "Depósito principal de la empresa",
            "parent_id": None
        },
        {
            "name": "Estantería A",
            "description": "Primera estantería del depósito",
            "parent_name": "Depósito Principal"
        },
        {
            "name": "Estante 1",
            "description": "Primer estante de la estantería A",
            "parent_name": "Estantería A"
        },
        {
            "name": "Estante 2",
            "description": "Segundo estante de la estantería A",
            "parent_name": "Estantería A"
        },
        {
            "name": "Estantería B",
            "description": "Segunda estantería del depósito",
            "parent_name": "Depósito Principal"
        },
        {
            "name": "Área de Recepción",
            "description": "Área temporal para equipos recién ingresados",
            "parent_id": None
        }
    ]
    
    created_locations = {}
    
    for location_data in locations_data:
        # Verificar si ya existe
        existing_location = db.query(Location).filter(
            Location.name == location_data["name"],
            Location.company_id == company.id
        ).first()
        
        if existing_location:
            logger.info(f"Ubicación {location_data['name']} ya existe")
            created_locations[location_data["name"]] = existing_location
            continue
        
        parent_id = None
        if "parent_name" in location_data:
            parent = created_locations.get(location_data["parent_name"])
            if parent:
                parent_id = parent.id
        
        location = Location(
            name=location_data["name"],
            description=location_data["description"],
            company_id=company.id,
            parent_id=parent_id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(location)
        db.commit()
        db.refresh(location)
        
        created_locations[location.name] = location
        logger.info(f"Ubicación creada: {location.name}")
    
    return list(created_locations.values())

def create_demo_tags(db: Session, company: Company):
    """Crear tags demo"""
    logger.info("Creando tags demo...")
    
    tags_data = [
        {"name": "Urgente", "color": "#dc3545", "description": "Equipos que requieren atención urgente"},
        {"name": "Frágil", "color": "#ffc107", "description": "Equipos que requieren manejo especial"},
        {"name": "Reparación", "color": "#fd7e14", "description": "Equipos en proceso de reparación"},
        {"name": "Garantía", "color": "#20c997", "description": "Equipos bajo garantía"},
        {"name": "VIP", "color": "#6f42c1", "description": "Cliente VIP"}
    ]
    
    created_tags = []
    
    for tag_data in tags_data:
        # Verificar si ya existe
        existing_tag = db.query(Tag).filter(
            Tag.name == tag_data["name"],
            Tag.company_id == company.id
        ).first()
        
        if existing_tag:
            logger.info(f"Tag {tag_data['name']} ya existe")
            created_tags.append(existing_tag)
            continue
        
        tag = Tag(
            name=tag_data["name"],
            color=tag_data["color"],
            description=tag_data["description"],
            company_id=company.id,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
        created_tags.append(tag)
        logger.info(f"Tag creado: {tag.name}")
    
    return created_tags

def create_demo_devices(db: Session, company: Company, locations: list, tags: list):
    """Crear dispositivos demo"""
    logger.info("Creando dispositivos demo...")
    
    devices_data = [
        {
            "name": "Laptop Dell Inspiron 15",
            "description": "Laptop Dell Inspiron 15 3000 Series",
            "serial_number": "DL123456789",
            "model": "Inspiron 15 3000",
            "brand": "Dell",
            "condition": DeviceCondition.BUENO,
            "status": DeviceStatus.ALMACENADO,
            "location_name": "Estante 1",
            "tag_names": ["Garantía"],
            "days_ago": 15
        },
        {
            "name": "PC Desktop HP",
            "description": "Computadora de escritorio HP Pavilion",
            "serial_number": "HP987654321",
            "model": "Pavilion Desktop",
            "brand": "HP",
            "condition": DeviceCondition.REGULAR,
            "status": DeviceStatus.ESPERANDO_RECIBIR,
            "location_name": "Área de Recepción",
            "tag_names": ["Reparación"],
            "days_ago": 3
        },
        {
            "name": "Monitor Samsung 24\"",
            "description": "Monitor Samsung 24 pulgadas Full HD",
            "serial_number": "SM456789123",
            "model": "S24F350",
            "brand": "Samsung",
            "condition": DeviceCondition.EXCELENTE,
            "status": DeviceStatus.INGRESADO,
            "location_name": "Área de Recepción",
            "tag_names": ["Frágil"],
            "days_ago": 1
        },
        {
            "name": "Impresora Canon",
            "description": "Impresora multifunción Canon PIXMA",
            "serial_number": "CN789123456",
            "model": "PIXMA MG3650",
            "brand": "Canon",
            "condition": DeviceCondition.MALO,
            "status": DeviceStatus.ENVIADO,
            "location_name": "Estante 2",
            "tag_names": ["Urgente", "Reparación"],
            "days_ago": 30
        },
        {
            "name": "Tablet iPad Air",
            "description": "Tablet Apple iPad Air 64GB",
            "serial_number": "AP321654987",
            "model": "iPad Air",
            "brand": "Apple",
            "condition": DeviceCondition.BUENO,
            "status": DeviceStatus.RETIRADO,
            "location_name": "Estante 1",
            "tag_names": ["VIP"],
            "days_ago": 45,
            "fecha_salida_days_ago": 5
        }
    ]
    
    # Crear mapeo de ubicaciones por nombre
    location_map = {loc.name: loc for loc in locations}
    tag_map = {tag.name: tag for tag in tags}
    
    created_devices = []
    
    for device_data in devices_data:
        # Verificar si ya existe
        existing_device = db.query(Device).filter(
            Device.serial_number == device_data["serial_number"],
            Device.company_id == company.id
        ).first()
        
        if existing_device:
            logger.info(f"Dispositivo {device_data['name']} ya existe")
            created_devices.append(existing_device)
            continue
        
        # Calcular fechas
        fecha_ingreso = now_local() - timedelta(days=device_data["days_ago"])
        fecha_salida = None
        if "fecha_salida_days_ago" in device_data:
            fecha_salida = now_local() - timedelta(days=device_data["fecha_salida_days_ago"])
        
        # Obtener ubicación
        location = location_map.get(device_data["location_name"])
        
        # Generar códigos
        qr_code = f"StoraTrack-{device_data['serial_number']}-{int(fecha_ingreso.timestamp())}"
        
        device = Device(
            name=device_data["name"],
            description=device_data["description"],
            serial_number=device_data["serial_number"],
            model=device_data["model"],
            brand=device_data["brand"],
            condition=device_data["condition"],
            status=device_data["status"],
            company_id=company.id,
            location_id=location.id if location else None,
            fecha_ingreso=fecha_ingreso,
            fecha_salida=fecha_salida,
            qr_code=qr_code,
            barcode=qr_code,
            is_active=True,
            created_at=fecha_ingreso
        )
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Agregar tags
        device_tags = [tag_map[tag_name] for tag_name in device_data["tag_names"] if tag_name in tag_map]
        device.tags = device_tags
        db.commit()
        
        # Crear movimiento inicial
        movement = DeviceMovement(
            device_id=device.id,
            to_status=device.status,
            to_location_id=device.location_id,
            notes=f"Dispositivo ingresado al sistema - {device.description}",
            moved_by="Sistema",
            created_at=fecha_ingreso
        )
        db.add(movement)
        
        # Si el dispositivo fue retirado, crear movimiento de salida
        if fecha_salida:
            exit_movement = DeviceMovement(
                device_id=device.id,
                from_status=DeviceStatus.ALMACENADO,
                to_status=DeviceStatus.RETIRADO,
                from_location_id=device.location_id,
                to_location_id=None,
                notes="Dispositivo retirado por el cliente",
                moved_by="Sistema",
                created_at=fecha_salida
            )
            db.add(exit_movement)
        
        db.commit()
        
        created_devices.append(device)
        logger.info(f"Dispositivo creado: {device.name} ({device.serial_number})")
    
    return created_devices

def init_database():
    """Inicializar base de datos con datos de prueba"""
    logger.info("Iniciando inicialización de base de datos...")
    
    # Crear tablas
    create_tables()
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Crear superadmin
        admin_user = create_superadmin(db)
        
        # Crear empresa demo
        demo_company = create_demo_company(db)
        
        # Crear usuarios demo
        demo_users = create_demo_users(db, demo_company)
        
        # Crear ubicaciones demo
        demo_locations = create_demo_locations(db, demo_company)
        
        # Crear tags demo
        demo_tags = create_demo_tags(db, demo_company)
        
        # Crear dispositivos demo
        demo_devices = create_demo_devices(db, demo_company, demo_locations, demo_tags)
        
        logger.info("\n" + "="*50)
        logger.info("INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        logger.info("="*50)
        logger.info(f"✓ Superadmin: {admin_user.email} / admin")
        logger.info(f"✓ Empresa demo: {demo_company.name}")
        logger.info(f"✓ Usuarios creados: {len(demo_users)}")
        logger.info(f"✓ Ubicaciones creadas: {len(demo_locations)}")
        logger.info(f"✓ Tags creados: {len(demo_tags)}")
        logger.info(f"✓ Dispositivos creados: {len(demo_devices)}")
        logger.info("\nCredenciales de acceso:")
        logger.info("- Superadmin: rodrantho@outlook.com / Kernel1.0")
        logger.info("- Staff: staff@demo.com / staff123")
        logger.info("- Cliente: cliente@demo.com / cliente123")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"Error durante la inicialización: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()