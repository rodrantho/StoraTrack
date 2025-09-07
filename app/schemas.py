from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, DeviceStatus, DeviceCondition

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True

# Company schemas
class CompanyBase(BaseModel):
    name: str
    rut_id: str
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    costo_base_default: float = 0.0
    costo_diario_default: float = 0.0
    logo_url: Optional[str] = None
    timezone: str = "America/Montevideo"
    currency: str = "UYU"
    iva_percent: float = 22.0
    incluir_iva: bool = True

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    costo_base_default: Optional[float] = None
    costo_diario_default: Optional[float] = None
    logo_url: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    iva_percent: Optional[float] = None
    incluir_iva: Optional[bool] = None
    is_active: Optional[bool] = None

class Company(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    company_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    company: Optional[Company] = None

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        if v and len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v

# Location schemas
class LocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None
    location_type: Optional[str] = "AREA"
    level: int = 1
    max_capacity: Optional[int] = None
    shelf_count: Optional[int] = None
    sort_order: int = 0

class LocationCreate(LocationBase):
    company_id: Optional[int] = None  # Empresa principal (opcional)
    company_ids: Optional[List[int]] = []  # Empresas con acceso

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None
    location_type: Optional[str] = None
    level: Optional[int] = None
    max_capacity: Optional[int] = None
    shelf_count: Optional[int] = None
    sort_order: Optional[int] = None
    company_id: Optional[int] = None
    company_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class Location(LocationBase):
    id: int
    company_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    children: List['Location'] = []
    companies: List['Company'] = []  # Empresas con acceso

    class Config:
        orm_mode = True

# Tag schemas
class TagBase(BaseModel):
    name: str
    color: str = "#007bff"
    description: Optional[str] = None

class TagCreate(TagBase):
    company_id: int

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Tag(TagBase):
    id: int
    company_id: int
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True

# Device schemas
class DeviceBase(BaseModel):
    name: str
    description: Optional[str] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    brand: Optional[str] = None
    status: DeviceStatus = DeviceStatus.INGRESADO
    condition: DeviceCondition = DeviceCondition.BUENO
    location_id: Optional[int] = None
    costo_base: Optional[float] = None
    costo_diario: Optional[float] = None

class DeviceCreate(DeviceBase):
    company_id: int
    tag_ids: List[int] = []

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    brand: Optional[str] = None
    status: Optional[DeviceStatus] = None
    condition: Optional[DeviceCondition] = None
    location_id: Optional[int] = None
    costo_base: Optional[float] = None
    costo_diario: Optional[float] = None
    fecha_salida: Optional[datetime] = None
    is_active: Optional[bool] = None
    tag_ids: Optional[List[int]] = None

class Device(DeviceBase):
    id: int
    company_id: int
    fecha_ingreso: datetime
    fecha_salida: Optional[datetime] = None
    photos: Optional[str] = None
    documents: Optional[str] = None
    qr_code: Optional[str] = None
    barcode: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    company: Optional[Company] = None
    location: Optional[Location] = None
    tags: List[Tag] = []

    class Config:
        orm_mode = True

# Device Movement schemas
class DeviceMovementBase(BaseModel):
    device_id: int
    from_location_id: Optional[int] = None
    to_location_id: Optional[int] = None
    from_status: Optional[DeviceStatus] = None
    to_status: DeviceStatus
    notes: Optional[str] = None
    moved_by: str

class DeviceMovementCreate(DeviceMovementBase):
    pass

class DeviceMovement(DeviceMovementBase):
    id: int
    created_at: datetime
    device: Optional[Device] = None
    from_location: Optional[Location] = None
    location: Optional[Location] = None

    class Config:
        orm_mode = True

# Cost Calculation schemas
class CostCalculationBase(BaseModel):
    device_id: int
    fecha_desde: datetime
    fecha_hasta: datetime
    dias_almacenados: int
    costo_base: float
    costo_diario: float
    subtotal: float
    iva_amount: float
    total: float

class CostCalculationCreate(CostCalculationBase):
    pass

class CostCalculation(CostCalculationBase):
    id: int
    calculated_at: datetime
    device: Optional[Device] = None

    class Config:
        orm_mode = True

# Monthly Report schemas
class MonthlyReportBase(BaseModel):
    company_id: int
    year: int
    month: int
    total_devices: int = 0
    total_cost: float = 0.0
    total_iva: float = 0.0
    total_with_iva: float = 0.0

class MonthlyReportCreate(MonthlyReportBase):
    pass

class MonthlyReport(MonthlyReportBase):
    id: int
    pdf_path: Optional[str] = None
    csv_path: Optional[str] = None
    is_closed: bool = False
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None
    created_at: datetime
    company: Optional[Company] = None

    class Config:
        orm_mode = True

# Audit Log schemas
class AuditLogBase(BaseModel):
    user_id: int
    action: str
    table_name: str
    record_id: Optional[int] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    created_at: datetime
    user: Optional[User] = None

    class Config:
        orm_mode = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Response schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int

# Dashboard schemas
class DashboardStats(BaseModel):
    total_companies: int
    total_devices: int
    total_users: int
    monthly_revenue: float

class CompanyDashboard(BaseModel):
    total_devices: int
    devices_by_status: dict
    monthly_cost: float
    recent_movements: List[DeviceMovement]

# Update Location schema to handle self-reference
Location.update_forward_refs()