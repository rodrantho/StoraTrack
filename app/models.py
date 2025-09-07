from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.utils.datetime_utils import now_local
import enum

Base = declarative_base()

# Tabla de asociación para la relación many-to-many entre Location y Company
location_company_association = Table(
    'location_companies',
    Base.metadata,
    Column('location_id', Integer, ForeignKey('locations.id'), primary_key=True),
    Column('company_id', Integer, ForeignKey('companies.id'), primary_key=True)
)

class UserRole(enum.Enum):
    SUPERADMIN = "superadmin"
    STAFF = "staff"
    CLIENT_USER = "client_user"

class DeviceStatus(enum.Enum):
    INGRESADO = "ingresado"
    ESPERANDO_RECIBIR = "esperando_recibir"
    ALMACENADO = "almacenado"
    ENVIADO = "enviado"
    RETIRADO = "retirado"

class DeviceCondition(enum.Enum):
    EXCELENTE = "excelente"
    BUENO = "bueno"
    REGULAR = "regular"
    MALO = "malo"
    PARA_REPARAR = "para_reparar"

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    rut_id = Column(String(50), unique=True, nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    
    # Costos por defecto
    costo_base_default = Column(Float, default=0.0)
    costo_diario_default = Column(Float, default=0.0)
    
    # Configuración
    logo_url = Column(String(500))
    timezone = Column(String(50), default="America/Montevideo")
    currency = Column(String(10), default="UYU")
    iva_percent = Column(Float, default=22.0)
    incluir_iva = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    updated_at = Column(DateTime, default=now_local, onupdate=now_local)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="company")
    devices = relationship("Device", back_populates="company")
    locations = relationship("Location", back_populates="primary_company")  # Ubicaciones donde es empresa principal
    shared_locations = relationship("Location", secondary=location_company_association, back_populates="companies")  # Ubicaciones compartidas
    tags = relationship("Tag", back_populates="company")
    monthly_reports = relationship("MonthlyReport", back_populates="company")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    
    # Company relationship (null for superadmin)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    updated_at = Column(DateTime, default=now_local, onupdate=now_local)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")

class LocationType(enum.Enum):
    DEPOSITO = "DEPOSITO"
    ESTANTERIA = "ESTANTERIA"
    ESTANTE = "ESTANTE"
    CAJA = "CAJA"
    AREA = "AREA"

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    code = Column(String(100))  # Código de referencia
    
    # Jerarquía y tipo
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    location_type = Column(Enum(LocationType), default=LocationType.AREA)
    level = Column(Integer, default=1)  # 1=deposito, 2=estanteria, 3=estante, 4=caja
    
    # Capacidad y organización
    max_capacity = Column(Integer)  # Capacidad máxima de equipos
    shelf_count = Column(Integer)  # Número de estantes (para estanterías)
    sort_order = Column(Integer, default=0)  # Para ordenar ubicaciones
    
    # Company relationship (many-to-many)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)  # Empresa principal (opcional)
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    updated_at = Column(DateTime, default=now_local, onupdate=now_local)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    primary_company = relationship("Company", back_populates="locations")  # Empresa principal
    companies = relationship("Company", secondary=location_company_association, back_populates="shared_locations")  # Empresas con acceso
    parent = relationship("Location", remote_side=[id], backref="children")
    devices = relationship("Device", back_populates="location")
    device_movements_from = relationship("DeviceMovement", foreign_keys="DeviceMovement.from_location_id", back_populates="from_location")
    device_movements_to = relationship("DeviceMovement", foreign_keys="DeviceMovement.to_location_id", back_populates="to_location")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#007bff")  # Hex color
    description = Column(Text)
    
    # Company relationship
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    company = relationship("Company", back_populates="tags")
    devices = relationship("Device", secondary="device_tags", back_populates="tags")

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Información básica
    name = Column(String(255), nullable=False)
    description = Column(Text)
    serial_number = Column(String(255))
    model = Column(String(255))
    brand = Column(String(255))
    
    # Estado y condición
    status = Column(Enum(DeviceStatus), default=DeviceStatus.INGRESADO)
    condition = Column(Enum(DeviceCondition), default=DeviceCondition.BUENO)
    
    # Fechas importantes
    fecha_ingreso = Column(DateTime, default=now_local)
    fecha_salida = Column(DateTime, nullable=True)
    
    # Costos específicos (si son diferentes a los default de la empresa)
    costo_base = Column(Float, nullable=True)
    costo_diario = Column(Float, nullable=True)
    
    # Ubicación actual
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    # Company relationship
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Archivos adjuntos
    photos = Column(Text)  # JSON array of photo URLs
    documents = Column(Text)  # JSON array of document URLs
    
    # QR/Barcode
    qr_code = Column(String(255))  # Generated QR code data
    barcode = Column(String(255))  # Generated barcode data
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    updated_at = Column(DateTime, default=now_local, onupdate=now_local)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    company = relationship("Company", back_populates="devices")
    location = relationship("Location", back_populates="devices")
    tags = relationship("Tag", secondary="device_tags", back_populates="devices")
    movements = relationship("DeviceMovement", back_populates="device")
    cost_calculations = relationship("CostCalculation", back_populates="device")

# Tabla de asociación para Device-Tag (many-to-many)
from sqlalchemy import Table
device_tags = Table(
    'device_tags',
    Base.metadata,
    Column('device_id', Integer, ForeignKey('devices.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class DeviceMovement(Base):
    __tablename__ = "device_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    
    # Movimiento
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    from_status = Column(Enum(DeviceStatus), nullable=True)
    to_status = Column(Enum(DeviceStatus), nullable=False)
    
    # Detalles
    notes = Column(Text)
    moved_by = Column(String(255))  # Usuario que realizó el movimiento
    
    # Timestamp
    created_at = Column(DateTime, default=now_local)
    
    # Relationships
    device = relationship("Device", back_populates="movements")
    from_location = relationship("Location", foreign_keys=[from_location_id], back_populates="device_movements_from")
    to_location = relationship("Location", foreign_keys=[to_location_id], back_populates="device_movements_to")

class CostCalculation(Base):
    __tablename__ = "cost_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    
    # Período de cálculo
    fecha_desde = Column(DateTime, nullable=False)
    fecha_hasta = Column(DateTime, nullable=False)
    dias_almacenados = Column(Integer, nullable=False)
    
    # Costos aplicados
    costo_base = Column(Float, nullable=False)
    costo_diario = Column(Float, nullable=False)
    
    # Cálculos
    subtotal = Column(Float, nullable=False)
    iva_amount = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    
    # Timestamp
    calculated_at = Column(DateTime, default=now_local)
    
    # Relationships
    device = relationship("Device", back_populates="cost_calculations")

class MonthlyReport(Base):
    __tablename__ = "monthly_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Período
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Resumen
    total_devices = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    total_iva = Column(Float, default=0.0)
    total_with_iva = Column(Float, default=0.0)
    
    # Archivos generados
    pdf_path = Column(String(500))
    csv_path = Column(String(500))
    
    # Estado
    is_closed = Column(Boolean, default=False)
    closed_at = Column(DateTime)
    closed_by = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    
    # Relationships
    company = relationship("Company", back_populates="monthly_reports")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Acción realizada
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    
    # Detalles
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=now_local)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class SystemConfig(Base):
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=now_local)
    updated_at = Column(DateTime, default=now_local, onupdate=now_local)