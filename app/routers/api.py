from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.utils.datetime_utils import now_local
from app.models import (
    User, Company, Device, Location, Tag, DeviceMovement, 
    MonthlyReport, UserRole, DeviceStatus
)
from app.schemas import (
    Company as CompanySchema, CompanyCreate, CompanyUpdate,
    User as UserSchema, UserCreate, UserUpdate,
    Device as DeviceSchema, DeviceCreate, DeviceUpdate,
    Location as LocationSchema, LocationCreate, LocationUpdate,
    Tag as TagSchema, TagCreate, TagUpdate,
    DeviceMovement as DeviceMovementSchema, DeviceMovementCreate,
    MonthlyReport as MonthlyReportSchema,
    PaginatedResponse, MessageResponse, DashboardStats, CompanyDashboard
)
from app.auth import (
    get_current_active_user, require_superadmin, require_admin_or_staff,
    check_company_access, get_password_hash
)
from app.config import settings

router = APIRouter()

# Companies API
@router.get("/companies", response_model=List[CompanySchema], tags=["Companies"])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Obtener lista de empresas"""
    companies = db.query(Company).filter(
        Company.is_active == True
    ).offset(skip).limit(limit).all()
    return companies

@router.post("/companies", response_model=CompanySchema, tags=["Companies"])
async def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear nueva empresa"""
    # Verificar que no exista el RUT
    existing = db.query(Company).filter(Company.rut_id == company.rut_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una empresa con ese RUT/ID"
        )
    
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/companies/{company_id}", response_model=CompanySchema, tags=["Companies"])
async def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Obtener empresa por ID"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    return company

@router.put("/companies/{company_id}", response_model=CompanySchema, tags=["Companies"])
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Actualizar empresa"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    update_data = company_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    company.updated_at = now_local()
    db.commit()
    db.refresh(company)
    return company

@router.delete("/companies/{company_id}", response_model=MessageResponse, tags=["Companies"])
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar empresa (soft delete)"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    company.is_active = False
    company.updated_at = datetime.utcnow()
    db.commit()
    
    return MessageResponse(message="Empresa eliminada exitosamente")

# Users API
@router.get("/users", response_model=List[UserSchema], tags=["Users"])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.max_page_size),
    company_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Obtener lista de usuarios"""
    query = db.query(User).filter(User.is_active == True)
    
    if company_id:
        query = query.filter(User.company_id == company_id)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=UserSchema, tags=["Users"])
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear nuevo usuario"""
    # Verificar que no exista el email
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )
    
    # Solo superadmin puede crear otros superadmin
    if user.role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear superadministradores"
        )
    
    user_data = user.dict()
    user_data['hashed_password'] = get_password_hash(user_data.pop('password'))
    
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Devices API
@router.get("/devices", response_model=List[DeviceSchema], tags=["Devices"])
async def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=settings.max_page_size),
    company_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de dispositivos"""
    query = db.query(Device).filter(Device.is_active == True)
    
    # Filtrar por empresa según permisos
    if current_user.role == UserRole.CLIENT_USER:
        if not current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario sin empresa asignada"
            )
        query = query.filter(Device.company_id == current_user.company_id)
    elif company_id:
        query = query.filter(Device.company_id == company_id)
    
    # Otros filtros
    if status:
        try:
            device_status = DeviceStatus(status)
            query = query.filter(Device.status == device_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Estado de dispositivo inválido"
            )
    
    if location_id:
        query = query.filter(Device.location_id == location_id)
    
    devices = query.offset(skip).limit(limit).all()
    return devices

@router.post("/devices", response_model=DeviceSchema, tags=["Devices"])
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear nuevo dispositivo"""
    # Verificar acceso a la empresa
    if not check_company_access(current_user, device.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta empresa"
        )
    
    device_data = device.dict()
    tag_ids = device_data.pop('tag_ids', [])
    
    db_device = Device(**device_data)
    
    # Agregar tags
    if tag_ids:
        tags = db.query(Tag).filter(
            Tag.id.in_(tag_ids),
            Tag.company_id == device.company_id,
            Tag.is_active == True
        ).all()
        db_device.tags = tags
    
    # Generar códigos QR y barcode
    qr_data = f"StoraTrack-{db_device.name}-{now_local().timestamp()}"
    db_device.qr_code = qr_data
    db_device.barcode = qr_data
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    # Crear movimiento inicial
    movement = DeviceMovement(
        device_id=db_device.id,
        to_status=db_device.status,
        to_location_id=db_device.location_id,
        notes="Dispositivo ingresado al sistema",
        moved_by=current_user.full_name
    )
    db.add(movement)
    db.commit()
    
    return db_device

@router.get("/devices/{device_id}", response_model=DeviceSchema, tags=["Devices"])
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener dispositivo por ID"""
    query = db.query(Device).filter(
        Device.id == device_id,
        Device.is_active == True
    )
    
    # Filtrar por empresa si es cliente
    if current_user.role == UserRole.CLIENT_USER:
        if not current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario sin empresa asignada"
            )
        query = query.filter(Device.company_id == current_user.company_id)
    
    device = query.first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo no encontrado"
        )
    
    return device

@router.put("/devices/{device_id}", response_model=DeviceSchema, tags=["Devices"])
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Actualizar dispositivo"""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo no encontrado"
        )
    
    # Verificar acceso a la empresa
    if not check_company_access(current_user, device.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta empresa"
        )
    
    update_data = device_update.dict(exclude_unset=True)
    tag_ids = update_data.pop('tag_ids', None)
    
    # Guardar valores anteriores para el movimiento
    old_status = device.status
    old_location_id = device.location_id
    
    # Actualizar campos
    for field, value in update_data.items():
        setattr(device, field, value)
    
    # Actualizar tags si se proporcionaron
    if tag_ids is not None:
        tags = db.query(Tag).filter(
            Tag.id.in_(tag_ids),
            Tag.company_id == device.company_id,
            Tag.is_active == True
        ).all()
        device.tags = tags
    
    device.updated_at = now_local()
    db.commit()
    
    # Crear movimiento si cambió estado o ubicación
    if (device.status != old_status or device.location_id != old_location_id):
        movement = DeviceMovement(
            device_id=device.id,
            from_status=old_status,
            to_status=device.status,
            from_location_id=old_location_id,
            to_location_id=device.location_id,
            notes="Dispositivo actualizado",
            moved_by=current_user.full_name
        )
        db.add(movement)
        db.commit()
    
    db.refresh(device)
    return device

# Locations API
@router.get("/locations", response_model=List[LocationSchema], tags=["Locations"])
async def get_locations(
    company_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener ubicaciones de una empresa o todas las ubicaciones para admin/staff"""
    # Si es admin o staff y no se especifica company_id, devolver todas las ubicaciones
    if current_user.role.value in ["superadmin", "staff"] and company_id is None:
        locations = db.query(Location).filter(
            Location.is_active == True
        ).all()
        return locations
    
    # Si se especifica company_id, verificar acceso
    if company_id:
        if not check_company_access(current_user, company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a esta empresa"
            )
        
        locations = db.query(Location).filter(
            Location.company_id == company_id,
            Location.is_active == True
        ).all()
        return locations
    
    # Para usuarios cliente sin company_id especificado, devolver error
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Debe especificar company_id"
    )

@router.post("/locations", response_model=LocationSchema, tags=["Locations"])
async def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear nueva ubicación"""
    # Verificar acceso a la empresa principal si se especifica
    if location.company_id and not check_company_access(current_user, location.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta empresa"
        )
    
    # Verificar acceso a las empresas con acceso
    if location.company_ids:
        for company_id in location.company_ids:
            if not check_company_access(current_user, company_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No tienes acceso a la empresa con ID {company_id}"
                )
    
    # Crear ubicación sin las company_ids (no es campo del modelo)
    location_data = location.dict(exclude={'company_ids'})
    db_location = Location(**location_data)
    db.add(db_location)
    db.flush()  # Para obtener el ID
    
    # Agregar empresas con acceso
    if location.company_ids:
        companies = db.query(Company).filter(Company.id.in_(location.company_ids)).all()
        db_location.companies = companies
    
    db.commit()
    db.refresh(db_location)
    return db_location

# Dashboard API
@router.get("/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Obtener estadísticas del dashboard"""
    total_companies = db.query(Company).filter(Company.is_active == True).count()
    total_devices = db.query(Device).filter(Device.is_active == True).count()
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # Calcular ingresos mensuales - suma de costos de todas las empresas
    from app.services.cost_calculator import CostCalculator
    from datetime import datetime
    
    monthly_revenue = 0.0
    try:
        calculator = CostCalculator(db)
        current_date = datetime.now()
        
        # Obtener todas las empresas activas
        active_companies = db.query(Company).filter(Company.is_active == True).all()
        
        for company in active_companies:
            try:
                # Calcular costo mensual de cada empresa
                company_monthly = calculator.calculate_company_monthly_cost(
                    company, current_date.year, current_date.month
                )
                monthly_revenue += company_monthly['total_cost']
            except Exception as e:
                # Si hay error con una empresa específica, continuar con las demás
                continue
                
    except Exception as e:
        # Si hay error general, mantener en 0
        monthly_revenue = 0.0
    
    return DashboardStats(
        total_companies=total_companies,
        total_devices=total_devices,
        total_users=total_users,
        monthly_revenue=monthly_revenue
    )

@router.get("/dashboard/company/{company_id}", response_model=CompanyDashboard, tags=["Dashboard"])
async def get_company_dashboard(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener dashboard de una empresa específica"""
    # Verificar acceso a la empresa
    if not check_company_access(current_user, company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta empresa"
        )
    
    total_devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).count()
    
    # Dispositivos por estado
    devices_by_status = {}
    for status in DeviceStatus:
        count = db.query(Device).filter(
            Device.company_id == company_id,
            Device.status == status,
            Device.is_active == True
        ).count()
        devices_by_status[status.value] = count
    
    # Movimientos recientes
    recent_movements = db.query(DeviceMovement).join(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).order_by(DeviceMovement.created_at.desc()).limit(10).all()
    
    # Costo mensual (simplificado)
    monthly_cost = 0.0  # Implementar cálculo real
    
    return CompanyDashboard(
        total_devices=total_devices,
        devices_by_status=devices_by_status,
        monthly_cost=monthly_cost,
        recent_movements=recent_movements
    )

# Cost calculation endpoint
@router.get("/devices/{device_id}/cost", tags=["Devices"])
async def calculate_device_cost(
    device_id: int,
    fecha_hasta: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calcular costo de un dispositivo hasta una fecha específica"""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo no encontrado"
        )
    
    # Verificar acceso a la empresa
    if not check_company_access(current_user, device.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta empresa"
        )
    
    if not fecha_hasta:
        fecha_hasta = now_local()
    
    # Calcular costo
    if device.fecha_salida and device.fecha_salida < fecha_hasta:
        fecha_hasta = device.fecha_salida
    
    dias = (fecha_hasta.date() - device.fecha_ingreso.date()).days + 1
    if dias < 1:
        dias = 1
    
    # Usar costos específicos del dispositivo o los default de la empresa
    costo_base = device.costo_base or device.company.costo_base_default
    costo_diario = device.costo_diario or device.company.costo_diario_default
    
    subtotal = costo_base + (costo_diario * dias)
    iva_amount = subtotal * (device.company.iva_percent / 100) if device.company.incluir_iva else 0
    total = subtotal + iva_amount
    
    return {
        "device_id": device_id,
        "fecha_desde": device.fecha_ingreso,
        "fecha_hasta": fecha_hasta,
        "dias_almacenados": dias,
        "costo_base": costo_base,
        "costo_diario": costo_diario,
        "subtotal": subtotal,
        "iva_percent": device.company.iva_percent,
        "iva_amount": iva_amount,
        "total": total,
        "currency": device.company.currency
    }