from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models import User, Company, Device, Location, Tag, UserRole, DeviceStatus, LocationType
from app.schemas import (
    CompanyCreate, CompanyUpdate, UserCreate, UserUpdate,
    LocationCreate, LocationUpdate, TagCreate, TagUpdate,
    DeviceCreate, DeviceUpdate
)
from app.auth import (
    require_admin_or_staff, 
    require_superadmin,
    get_current_active_user,
    get_password_hash,
    check_company_access
)
from app.config import settings
from app.utils.datetime_utils import now_local
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Función auxiliar para calcular costos de dispositivos
def calculate_device_cost(device: Device, fecha_hasta: datetime = None) -> float:
    """Calcular costo de un dispositivo hasta una fecha"""
    try:
        if fecha_hasta is None:
            fecha_hasta = now_local()
            
        if device.fecha_salida and device.fecha_salida < fecha_hasta:
            fecha_hasta = device.fecha_salida
        
        # Convertir fechas a date si es necesario
        fecha_ingreso = device.fecha_ingreso.date() if hasattr(device.fecha_ingreso, 'date') else device.fecha_ingreso
        fecha_hasta_date = fecha_hasta.date() if hasattr(fecha_hasta, 'date') else fecha_hasta
        
        dias = (fecha_hasta_date - fecha_ingreso).days + 1
        if dias < 1:
            dias = 1
        
        # Usar costos específicos del dispositivo o los default de la empresa
        costo_base = device.costo_base or device.company.costo_base_default or 0.0
        costo_diario = device.costo_diario or device.company.costo_diario_default or 0.0
        
        subtotal = costo_base + (costo_diario * dias)
        iva_amount = subtotal * (device.company.iva_percent / 100) if device.company.incluir_iva else 0
        total = subtotal + iva_amount
        
        return total
    except Exception as e:
        print(f"Error in calculate_device_cost for device {device.id}: {e}")
        return 0.0

# Dashboard
@router.get("/dashboard", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Dashboard de administración"""
    # Estadísticas generales
    total_companies = db.query(Company).filter(Company.is_active == True).count()
    total_devices = db.query(Device).filter(Device.is_active == True).count()
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # Dispositivos por estado
    from app.models import DeviceStatus
    devices_by_status = {}
    for status in DeviceStatus:
        count = db.query(Device).filter(
            Device.status == status,
            Device.is_active == True
        ).count()
        devices_by_status[status.value] = count
    
    # Empresas recientes
    recent_companies = db.query(Company).filter(
        Company.is_active == True
    ).order_by(Company.created_at.desc()).limit(5).all()
    
    # Usuarios recientes
    recent_users = db.query(User).filter(
        User.is_active == True
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Estadísticas de ubicaciones
    from app.models import Location
    total_locations = db.query(Location).filter(Location.is_active == True).count()
    
    # Ubicaciones con equipos
    locations_with_devices = db.query(Location).join(Device).filter(
        Location.is_active == True,
        Device.is_active == True
    ).distinct().count()
    
    # Ubicaciones vacías
    empty_locations = total_locations - locations_with_devices
    
    # Ubicaciones sobre capacidad (donde hay más equipos que la capacidad máxima)
    over_capacity_locations = db.query(Location).filter(
        Location.is_active == True,
        Location.max_capacity.isnot(None),
        Location.max_capacity > 0
    ).all()
    
    over_capacity_count = 0
    for location in over_capacity_locations:
        device_count = db.query(Device).filter(
            Device.location_id == location.id,
            Device.is_active == True
        ).count()
        if device_count > location.max_capacity:
            over_capacity_count += 1
    
    # Ubicaciones recientes
    recent_locations = db.query(Location).filter(
        Location.is_active == True
    ).order_by(Location.created_at.desc()).limit(5).all()
    
    # Agregar información de empresas y dispositivos a las ubicaciones recientes
    for location in recent_locations:
        # Contar dispositivos en esta ubicación
        location.device_count = db.query(Device).filter(
            Device.location_id == location.id,
            Device.is_active == True
        ).count()
        
        # Calcular porcentaje de capacidad
        if location.max_capacity and location.max_capacity > 0:
            location.capacity_percentage = min(100, (location.device_count / location.max_capacity) * 100)
        else:
            location.capacity_percentage = 0
    
    # Obtener todas las ubicaciones y empresas para los modales
    locations = db.query(Location).filter(Location.is_active == True).all()
    companies = db.query(Company).filter(Company.is_active == True).all()

    # Crear objeto stats para el template
    stats = {
        "total_companies": total_companies,
        "total_devices": total_devices,
        "total_users": total_users,
        "monthly_revenue": 0.0,  # Placeholder para ingresos mensuales
        "total_locations": total_locations,
        "locations_with_devices": locations_with_devices,
        "empty_locations": empty_locations,
        "over_capacity_locations": over_capacity_count
    }

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "current_user": current_user,
        "stats": stats,
        "devices_by_status": devices_by_status,
        "recent_companies": recent_companies,
        "recent_users": recent_users,
        "recent_locations": recent_locations,
        "locations": locations,
        "companies": companies
    })

# Gestión de empresas
@router.get("/companies", response_class=HTMLResponse, name="admin_companies")
async def list_companies(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Listar empresas"""
    page_size = settings.default_page_size
    offset = (page - 1) * page_size
    
    companies = db.query(Company).filter(
        Company.is_active == True
    ).offset(offset).limit(page_size).all()
    
    total = db.query(Company).filter(Company.is_active == True).count()
    pages = (total + page_size - 1) // page_size
    
    return templates.TemplateResponse("admin/companies.html", {
        "request": request,
        "current_user": current_user,
        "companies": companies,
        "page": page,
        "pages": pages,
        "total": total
    })

@router.get("/companies/new", response_class=HTMLResponse, name="admin_company_new")
async def new_company_form(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Formulario nueva empresa"""
    return templates.TemplateResponse("admin/company_edit.html", {
        "request": request,
        "current_user": current_user,
        "company": None,
        "action": "create"
    })

@router.post("/companies/new", name="admin_company_create")
async def create_company(
    request: Request,
    name: str = Form(...),
    rut_id: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    costo_base_default: float = Form(0.0),
    costo_diario_default: float = Form(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear empresa"""
    # Verificar que no exista el RUT
    existing = db.query(Company).filter(Company.rut_id == rut_id).first()
    if existing:
        return templates.TemplateResponse("admin/company_edit.html", {
            "request": request,
            "current_user": current_user,
            "company": None,
            "action": "create",
            "error": "Ya existe una empresa con ese RUT/ID"
        })
    
    company = Company(
        name=name,
        rut_id=rut_id,
        contact_name=contact_name or None,
        email=email or None,
        phone=phone or None,
        address=address or None,
        costo_base_default=costo_base_default,
        costo_diario_default=costo_diario_default
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    
    return RedirectResponse(url="/admin/companies", status_code=302)

@router.get("/companies/{company_id}", response_class=HTMLResponse, name="admin_company_detail")
async def view_company(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Ver empresa"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Estadísticas de la empresa
    total_devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).count()
    
    total_users = db.query(User).filter(
        User.company_id == company_id,
        User.is_active == True
    ).count()
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Empresas", "url": "/admin/companies"},
        {"title": company.name, "url": ""}
    ]
    
    return templates.TemplateResponse("admin/company_detail.html", {
        "request": request,
        "current_user": current_user,
        "company": company,
        "total_devices": total_devices,
        "total_users": total_users,
        "breadcrumbs": breadcrumbs,
        "back_url": "/admin/companies"
    })

@router.get("/companies/{company_id}/edit", response_class=HTMLResponse, name="admin_company_edit")
async def edit_company_form(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Formulario editar empresa"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Empresas", "url": "/admin/companies"},
        {"title": company.name, "url": f"/admin/companies/{company_id}"},
        {"title": "Editar", "url": ""}
    ]
    
    return templates.TemplateResponse("admin/company_edit.html", {
        "request": request,
        "current_user": current_user,
        "company": company,
        "action": "edit",
        "breadcrumbs": breadcrumbs,
        "back_url": f"/admin/companies/{company_id}"
    })

@router.post("/companies/{company_id}/edit", name="admin_company_update")
async def update_company(
    request: Request,
    company_id: int,
    name: str = Form(...),
    contact_name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    costo_base_default: float = Form(0.0),
    costo_diario_default: float = Form(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Actualizar empresa"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    company.name = name
    company.contact_name = contact_name or None
    company.email = email or None
    company.phone = phone or None
    company.address = address or None
    company.costo_base_default = costo_base_default
    company.costo_diario_default = costo_diario_default
    
    company.updated_at = now_local()
    
    db.commit()
    
    return RedirectResponse(url=f"/admin/companies/{company_id}", status_code=302)

@router.post("/companies/{company_id}/delete", name="admin_company_delete")
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar empresa (desactivar)"""
    print(f"Intentando eliminar empresa con ID: {company_id}")
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar que no tenga dispositivos activos
    active_devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).count()
    
    print(f"Dispositivos activos encontrados: {active_devices}")
    
    if active_devices > 0:
        print("No se puede eliminar: tiene dispositivos activos")
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar una empresa con dispositivos activos"
        )
    
    print("Desactivando empresa...")
    company.is_active = False
    company.updated_at = now_local()
    db.commit()
    print("Empresa desactivada exitosamente")
    
    return RedirectResponse(url="/admin/companies", status_code=302)

@router.get("/companies/{company_id}/delete", name="admin_company_delete_get")  # Ruta GET adicional para depuración
async def delete_company_get(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar empresa (desactivar)"""
    print(f"Intentando eliminar empresa con ID: {company_id}")
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar que no tenga dispositivos activos
    active_devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).count()
    
    print(f"Dispositivos activos encontrados: {active_devices}")
    
    if active_devices > 0:
        print("No se puede eliminar: tiene dispositivos activos")
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar una empresa con dispositivos activos"
        )
    
    print("Desactivando empresa...")
    company.is_active = False
    company.updated_at = now_local()
    db.commit()
    print("Empresa desactivada exitosamente")
    
    return RedirectResponse(url="/admin/companies", status_code=302)

# Gestión de usuarios
@router.get("/users", response_class=HTMLResponse, name="admin_users")
async def list_users(
    request: Request,
    page: int = 1,
    company_id: Optional[int] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Listar usuarios"""
    page_size = settings.default_page_size
    offset = (page - 1) * page_size
    
    query = db.query(User).filter(User.is_active == True)
    
    if company_id:
        query = query.filter(User.company_id == company_id)
    
    users = query.offset(offset).limit(page_size).all()
    total = query.count()
    pages = (total + page_size - 1) // page_size
    
    # Obtener empresas para filtro
    companies = db.query(Company).filter(Company.is_active == True).all()
    
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "companies": companies,
        "selected_company_id": company_id,
        "page": page,
        "pages": pages,
        "total": total,
        "error": error
    })

# GET route for /users/create removed - user creation is handled via modal on /admin/users page

@router.post("/users/create", name="admin_user_create")
async def create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    company_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear usuario"""
    # Verificar que no exista el email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        # Redirigir con mensaje de error
        return RedirectResponse(url="/admin/users?error=Ya+existe+un+usuario+con+ese+email", status_code=302)
    
    # Validar rol
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rol inválido")
    
    # Solo superadmin puede crear otros superadmin
    if user_role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear superadministradores")

    # Convertir company_id a int si no está vacío
    final_company_id = None
    if company_id and company_id.strip():
        try:
            final_company_id = int(company_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de empresa inválido")
    
    # Validar que CLIENT_USER tenga empresa asignada
    if user_role == UserRole.CLIENT_USER and not final_company_id:
        return RedirectResponse(url="/admin/users?error=Los+usuarios+cliente+deben+tener+una+empresa+asignada", status_code=302)

    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=user_role,
        company_id=final_company_id if user_role != UserRole.SUPERADMIN else None
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.get("/users/{user_id}", response_class=HTMLResponse, name="admin_user_detail")
async def view_user(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Ver detalles de usuario o redirigir si es 'create'"""
    # Manejar caso especial de 'create'
    if user_id == "create":
        return RedirectResponse(url="/admin/users", status_code=302)
    
    # Convertir a entero para búsqueda normal
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Usuarios", "url": "/admin/users"},
        {"title": user.full_name, "url": ""}
    ]
    
    return templates.TemplateResponse("admin/user_detail.html", {
        "request": request,
        "current_user": current_user,
        "user": user,
        "breadcrumbs": breadcrumbs,
        "back_url": "/admin/users"
    })

@router.get("/users/{user_id}/edit", response_class=HTMLResponse, name="admin_user_edit")
async def edit_user(
    request: Request,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Formulario de edición de usuario"""
    # Convertir a entero
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    companies = db.query(Company).filter(Company.is_active == True).all()
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Usuarios", "url": "/admin/users"},
        {"title": user.full_name, "url": f"/admin/users/{user_id}"},
        {"title": "Editar", "url": ""}
    ]
    
    return templates.TemplateResponse("admin/user_edit.html", {
        "request": request,
        "current_user": current_user,
        "user": user,
        "companies": companies,
        "action": "edit",
        "user_roles": UserRole,
        "breadcrumbs": breadcrumbs,
        "back_url": f"/admin/users/{user_id}"
    })

@router.post("/users/{user_id}/edit", name="admin_user_update")
async def update_user(
    request: Request,
    user_id: str,
    email: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    company_id: Optional[int] = Form(None),
    password: str = Form(""),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Actualizar usuario"""
    # Convertir a entero
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Si el usuario actual es staff, no puede cambiar roles a super admin
    if current_user.role == UserRole.STAFF and role == "superadmin":
        companies = db.query(Company).filter(Company.is_active == True).all()
        return templates.TemplateResponse("admin/user_edit.html", {
            "request": request,
            "current_user": current_user,
            "user": user,
            "companies": companies,
            "action": "edit",
            "user_roles": UserRole,
            "error": "Los usuarios staff no pueden crear super admins"
        }, status_code=403)
    
    # Verificar email único
    existing_user = db.query(User).filter(
        User.email == email,
        User.id != user_id
    ).first()
    if existing_user:
        companies = db.query(Company).filter(Company.is_active == True).all()
        return templates.TemplateResponse("admin/user_edit.html", {
            "request": request,
            "current_user": current_user,
            "user": user,
            "companies": companies,
            "action": "edit",
            "user_roles": UserRole,
            "error": "El email ya está en uso"
        }, status_code=400)
    
    # Actualizar datos
    user.email = email
    user.full_name = full_name
    user.role = UserRole(role)
    user.company_id = company_id
    user.is_active = is_active
    
    if password:
        user.hashed_password = get_password_hash(password)
    
    user.updated_at = now_local()
    db.commit()
    
    return RedirectResponse(url=f"/admin/users/{user_id}", status_code=302)

@router.post("/users/{user_id}/delete", name="admin_user_delete")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar usuario (desactivar)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir eliminar el propio usuario
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puede eliminar su propio usuario")
    
    # Staff no puede eliminar otros staff o superadmin
    if current_user.role == UserRole.STAFF and user.role in [UserRole.STAFF, UserRole.SUPERADMIN]:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar usuarios staff o superadmin")
    
    user.is_active = False
    user.updated_at = now_local()
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)

@router.get("/users/new", response_class=HTMLResponse, name="admin_user_new")
async def new_user_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Redirigir a la página de usuarios (el formulario está en modal)"""
    return RedirectResponse(url="/admin/users", status_code=302)

# Esta ruta ha sido reemplazada por /users/create

# Etiquetas
@router.get("/labels", response_class=HTMLResponse, name="admin_labels")
async def labels_page(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de generación de etiquetas"""
    return templates.TemplateResponse(
        "admin/labels.html",
        {"request": request, "current_user": current_user}
    )

# Dispositivos
@router.get("/devices", response_class=HTMLResponse, name="admin_devices")
async def devices_page(
    request: Request,
    search: Optional[str] = None,
    status: Optional[str] = None,
    company: Optional[int] = None,
    location: Optional[int] = None,
    sort: str = "created_at",
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de gestión de dispositivos"""
    # Calcular estadísticas de resumen
    total_devices = db.query(Device).filter(Device.is_active == True).count()
    stored_devices = db.query(Device).filter(
        Device.is_active == True,
        Device.status == DeviceStatus.ALMACENADO
    ).count()
    in_process_devices = db.query(Device).filter(
        Device.is_active == True,
        Device.status.in_([DeviceStatus.INGRESADO, DeviceStatus.ESPERANDO_RECIBIR])
    ).count()
    
    # Calcular valor total (placeholder)
    total_value = 0.0
    
    summary = {
        "total": total_devices,
        "stored": stored_devices,
        "in_process": in_process_devices,
        "total_value": total_value
    }
    
    # Construir query base para dispositivos
    query = db.query(Device).filter(Device.is_active == True)
    
    # Aplicar filtros
    if search:
        query = query.filter(
            Device.name.ilike(f"%{search}%") |
            Device.serial_number.ilike(f"%{search}%") |
            Device.brand.ilike(f"%{search}%") |
            Device.model.ilike(f"%{search}%")
        )
    
    if status:
        try:
            device_status = DeviceStatus(status.lower())
            query = query.filter(Device.status == device_status)
        except ValueError:
            pass
    
    if company:
        query = query.filter(Device.company_id == company)
    
    if location:
        query = query.filter(Device.location_id == location)
    
    # Aplicar ordenamiento
    if sort == "name":
        query = query.order_by(Device.name)
    elif sort == "status":
        query = query.order_by(Device.status)
    elif sort == "company":
        query = query.join(Company).order_by(Company.name)
    else:  # created_at
        query = query.order_by(Device.created_at.desc())
    
    # Paginación
    per_page = 20
    total_devices = query.count()
    total_pages = (total_devices + per_page - 1) // per_page
    offset = (page - 1) * per_page
    devices = query.offset(offset).limit(per_page).all()
    
    # Crear objeto de paginación
    pagination = {
        "page": page,
        "pages": total_pages,
        "per_page": per_page,
        "total": total_devices,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_num": page - 1 if page > 1 else None,
        "next_num": page + 1 if page < total_pages else None
    }
    
    # Obtener empresas y ubicaciones para los filtros y modales
    companies = db.query(Company).filter(Company.is_active == True).all()
    locations = db.query(Location).filter(Location.is_active == True).all()
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Equipos", "url": ""}
    ]
    
    return templates.TemplateResponse(
        "admin/devices.html",
        {
            "request": request, 
            "current_user": current_user,
            "summary": summary,
            "devices": devices,
            "companies": companies,
            "locations": locations,
            "breadcrumbs": breadcrumbs,
            "pagination": pagination,
            "now": now_local(),
            "calculate_device_cost": calculate_device_cost
        }
    )

@router.post("/devices", name="admin_device_create")
async def create_device(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear nuevo dispositivo desde formulario HTML"""
    try:
        # Obtener datos del formulario
        form_data = await request.form()
        data = dict(form_data)
        
        # Validar campos requeridos
        if not data.get('name'):
            return {"success": False, "message": "El nombre del equipo es requerido"}
        
        if not data.get('company_id'):
            return {"success": False, "message": "La empresa es requerida"}
        
        # Convertir company_id a int
        try:
            company_id = int(data['company_id'])
        except (ValueError, TypeError):
            return {"success": False, "message": "ID de empresa inválido"}
        
        # Verificar acceso a la empresa
        from app.auth import check_company_access
        if not check_company_access(current_user, company_id):
            return {"success": False, "message": "No tienes acceso a esta empresa"}
        
        # Convertir location_id si existe
        location_id = None
        if data.get('location_id'):
            try:
                location_id = int(data['location_id'])
            except (ValueError, TypeError):
                pass
        
        # Crear dispositivo
        device_data = {
            'name': data['name'],
            'company_id': company_id,
            'description': data.get('description', ''),
            'serial_number': data.get('serial_number', ''),
            'model': data.get('model', ''),
            'brand': data.get('brand', ''),
            'status': DeviceStatus(data.get('status', 'ALMACENADO')),
            'condition': data.get('condition') if data.get('condition') else None,
            'location_id': location_id
        }
        
        db_device = Device(**device_data)
        
        # Generar códigos QR y barcode
        qr_data = f"StoraTrack-{db_device.name}-{now_local().timestamp()}"
        db_device.qr_code = qr_data
        db_device.barcode = qr_data
        
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        # Crear movimiento inicial
        from app.models import DeviceMovement
        movement = DeviceMovement(
            device_id=db_device.id,
            to_status=db_device.status,
            to_location_id=db_device.location_id,
            notes="Dispositivo ingresado al sistema",
            moved_by=current_user.full_name
        )
        db.add(movement)
        db.commit()
        
        return {"success": True, "message": "Equipo creado exitosamente"}
        
    except Exception as e:
        db.rollback()
        print(f"Error creating device: {str(e)}")
        return {"success": False, "message": f"Error al crear el equipo: {str(e)}"}

@router.get("/devices/new", response_class=HTMLResponse, name="admin_device_new")
async def new_device_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Redirigir a la página de dispositivos (el formulario está en modal)"""
    return RedirectResponse(url="/admin/devices", status_code=302)

@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar un dispositivo específico"""
    try:
        # Buscar el dispositivo
        device = db.query(Device).filter(
            Device.id == device_id,
            Device.is_active == True
        ).first()
        
        if not device:
            return {"success": False, "message": "Dispositivo no encontrado"}
        
        # Verificar acceso a la empresa
        from app.auth import check_company_access
        if not check_company_access(current_user, device.company_id):
            return {"success": False, "message": "No tienes acceso a este dispositivo"}
        
        # Eliminar el dispositivo (soft delete)
        device.is_active = False
        device.updated_at = now_local()
        
        db.commit()
        
        return {"success": True, "message": "Dispositivo eliminado exitosamente"}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al eliminar el dispositivo: {str(e)}"}

# Ubicaciones
@router.get("/locations", response_class=HTMLResponse, name="admin_locations")
async def locations_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de gestión de ubicaciones"""
    # Calcular estadísticas de resumen
    total_locations = db.query(Location).filter(Location.is_active == True).count()
    root_locations = db.query(Location).filter(
        Location.is_active == True,
        Location.parent_id == None
    ).count()
    child_locations = total_locations - root_locations
    
    # Obtener empresas para el selector
    companies = db.query(Company).filter(Company.is_active == True).all()
    
    # Obtener ubicaciones con jerarquía
    locations = db.query(Location).filter(
        Location.is_active == True
    ).order_by(Location.parent_id.asc(), Location.sort_order.asc(), Location.name.asc()).all()
    
    summary = {
        "total": total_locations,
        "root": root_locations,
        "children": child_locations,
        "total_value": 0.0
    }
    
    return templates.TemplateResponse(
        "admin/locations.html",
        {
            "request": request, 
            "current_user": current_user,
            "companies": companies,
            "locations": locations,
            "summary": summary
        }
    )

# Tags
@router.get("/tags", response_class=HTMLResponse, name="admin_tags")
async def tags_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de gestión de tags"""
    # Calcular estadísticas de resumen
    total_tags = db.query(Tag).filter(Tag.is_active == True).count()
    
    # Placeholder para estadísticas más complejas
    in_use_tags = 0  # Requiere consulta a tabla de relaciones
    most_used_count = 0  # Requiere consulta agregada
    
    summary = {
        "total": total_tags,
        "in_use": in_use_tags,
        "most_used_count": most_used_count,
        "total_value": 0.0
    }
    
    return templates.TemplateResponse(
        "admin/tags.html",
        {
            "request": request, 
            "current_user": current_user,
            "summary": summary
        }
    )

@router.post("/users/{user_id}/change-role")
async def change_user_role(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Cambiar el rol de un usuario"""
    try:
        # Obtener datos del request
        data = await request.json()
        new_role = data.get("role")
        
        if not new_role or new_role not in ["superadmin", "staff", "client_user"]:
            raise HTTPException(status_code=400, detail="Rol inválido")
        
        # Si el usuario actual es staff, no puede crear super admins
        if current_user.role == UserRole.STAFF and new_role == "superadmin":
            raise HTTPException(status_code=403, detail="Los usuarios staff no pueden crear super admins")
        
        # Buscar el usuario
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # No permitir que un usuario cambie su propio rol
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol")
        
        # Actualizar el rol
        user.role = new_role
        
        # Si el nuevo rol no es client_user, limpiar company_id
        if new_role != "client_user":
            user.company_id = None
        
        db.commit()
        
        return {"message": "Rol actualizado exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/locations/{location_id}", response_class=HTMLResponse, name="admin_location_detail")
async def location_detail_page(
    location_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de detalles de una ubicación específica"""
    try:
        location = db.query(Location).filter(
            Location.id == location_id,
            Location.is_active == True
        ).first()
        
        if not location:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        
        # Verificar acceso si la ubicación tiene empresa asignada
        if location.company_id and not check_company_access(current_user, location.company_id):
            raise HTTPException(status_code=403, detail="No tienes acceso a esta ubicación")
        
        # Obtener dispositivos en esta ubicación
        devices = db.query(Device).filter(
            Device.location_id == location_id,
            Device.is_active == True
        ).all()
        
        # Obtener sub-ubicaciones
        children = db.query(Location).filter(
            Location.parent_id == location_id,
            Location.is_active == True
        ).all()
        
        # Breadcrumbs
        breadcrumbs = [
            {"title": "Dashboard", "url": "/admin/dashboard"},
            {"title": "Ubicaciones", "url": "/admin/locations"},
            {"title": location.name, "url": ""}
        ]
        
        return templates.TemplateResponse("admin/location_detail.html", {
            "request": request,
            "current_user": current_user,
            "location": location,
            "devices": devices,
            "children": children,
            "breadcrumbs": breadcrumbs,
            "back_url": "/admin/locations"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/locations/{location_id}/data")
async def get_location_data(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Obtener datos JSON de una ubicación específica"""
    try:
        location = db.query(Location).filter(
            Location.id == location_id,
            Location.is_active == True
        ).first()
        
        if not location:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        
        # Verificar acceso si la ubicación tiene empresa asignada
        if location.company_id and not check_company_access(current_user, location.company_id):
            raise HTTPException(status_code=403, detail="No tienes acceso a esta ubicación")
        
        # Preparar respuesta
        location_data = {
            "id": location.id,
            "name": location.name,
            "description": location.description,
            "code": location.code,
            "location_type": location.location_type.value if location.location_type else None,
            "max_capacity": location.max_capacity,
            "shelf_count": location.shelf_count,
            "parent_id": location.parent_id,
            "company_id": location.company_id,
            "created_at": location.created_at.isoformat() if location.created_at else None,
            "primary_company": {
                "id": location.primary_company.id,
                "name": location.primary_company.name
            } if location.primary_company else None,
            "parent": {
                "id": location.parent.id,
                "name": location.parent.name
            } if location.parent else None
        }
        
        return location_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/locations/{location_id}")
async def update_location(
    location_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Actualizar una ubicación específica"""
    try:
        # Buscar la ubicación
        location = db.query(Location).filter(
            Location.id == location_id,
            Location.is_active == True
        ).first()
        
        if not location:
            return {"success": False, "message": "Ubicación no encontrada"}
        
        # Verificar acceso
        if location.company_id and not check_company_access(current_user, location.company_id):
            return {"success": False, "message": "No tienes acceso a esta ubicación"}
        
        # Obtener datos del formulario
        data = await request.json()
        
        # Validar campos requeridos
        if not data.get("name"):
            return {"success": False, "message": "El nombre es requerido"}
        
        # Convertir tipos
        company_id = int(data["company_id"]) if data.get("company_id") and data["company_id"] != "" else None
        parent_id = int(data["parent_id"]) if data.get("parent_id") and data["parent_id"] != "" else None
        max_capacity = int(data["max_capacity"]) if data.get("max_capacity") and data["max_capacity"] != "" else None
        shelf_count = int(data["shelf_count"]) if data.get("shelf_count") and data["shelf_count"] != "" else None
        
        # Verificar acceso a la nueva empresa si se especifica
        if company_id and not check_company_access(current_user, company_id):
            return {"success": False, "message": "No tienes acceso a esta empresa"}
        
        # Actualizar campos
        location.name = data["name"]
        location.description = data.get("description")
        location.code = data.get("code")
        location.parent_id = parent_id
        location.location_type = LocationType(data.get("location_type", "AREA"))
        location.max_capacity = max_capacity
        location.shelf_count = shelf_count
        location.company_id = company_id
        
        db.commit()
        
        return {"success": True, "message": "Ubicación actualizada exitosamente"}
        
    except ValueError as e:
        return {"success": False, "message": f"Error de validación: {str(e)}"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al actualizar la ubicación: {str(e)}"}

@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar una ubicación específica"""
    try:
        # Buscar la ubicación
        location = db.query(Location).filter(
            Location.id == location_id,
            Location.is_active == True
        ).first()
        
        if not location:
            return {"success": False, "message": "Ubicación no encontrada"}
        
        # Verificar acceso
        if location.company_id and not check_company_access(current_user, location.company_id):
            return {"success": False, "message": "No tienes acceso a esta ubicación"}
        
        # Verificar si tiene dispositivos asociados
        device_count = db.query(Device).filter(
            Device.location_id == location_id,
            Device.is_active == True
        ).count()
        
        if device_count > 0:
            return {"success": False, "message": f"No se puede eliminar la ubicación porque tiene {device_count} dispositivos asociados"}
        
        # Verificar si tiene sub-ubicaciones
        child_count = db.query(Location).filter(
            Location.parent_id == location_id,
            Location.is_active == True
        ).count()
        
        if child_count > 0:
            return {"success": False, "message": f"No se puede eliminar la ubicación porque tiene {child_count} sub-ubicaciones"}
        
        # Marcar como inactiva (soft delete)
        location.is_active = False
        db.commit()
        
        return {"success": True, "message": "Ubicación eliminada exitosamente"}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al eliminar la ubicación: {str(e)}"}

@router.get("/locations/{location_id}/edit", response_class=HTMLResponse, name="admin_location_edit")
async def edit_location_form(
    request: Request,
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Formulario de edición de ubicación"""
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.is_active == True
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    # Verificar acceso
    if location.company_id and not check_company_access(current_user, location.company_id):
        raise HTTPException(status_code=403, detail="No tienes acceso a esta ubicación")
    
    companies = db.query(Company).filter(Company.is_active == True).all()
    locations = db.query(Location).filter(
        Location.is_active == True,
        Location.id != location_id  # Excluir la ubicación actual para evitar ciclos
    ).all()
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Ubicaciones", "url": "/admin/locations"},
        {"title": location.name, "url": f"/admin/locations/{location_id}"},
        {"title": "Editar", "url": ""}
    ]
    
    return templates.TemplateResponse("admin/location_edit.html", {
        "request": request,
        "current_user": current_user,
        "location": location,
        "companies": companies,
        "locations": locations,
        "action": "edit",
        "location_types": LocationType,
        "breadcrumbs": breadcrumbs,
        "back_url": f"/admin/locations/{location_id}"
    })

@router.post("/locations")
async def admin_location_create(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear nueva ubicación desde el panel de administración"""
    try:
        # Obtener datos del formulario
        data = await request.json()
        
        # Validar campos requeridos
        if not data.get("name"):
            return {"success": False, "message": "El nombre es requerido"}
        
        # Convertir tipos
        company_id = int(data["company_id"]) if data.get("company_id") and data["company_id"] != "" else None
        parent_id = int(data["parent_id"]) if data.get("parent_id") and data["parent_id"] != "" else None
        max_capacity = int(data["max_capacity"]) if data.get("max_capacity") and data["max_capacity"] != "" else None
        shelf_count = int(data["shelf_count"]) if data.get("shelf_count") and data["shelf_count"] != "" else None
        sort_order = int(data.get("sort_order", 0))
        
        # Verificar acceso a la empresa principal si se especifica
        if company_id and not check_company_access(current_user, company_id):
            return {"success": False, "message": "No tienes acceso a esta empresa"}
        
        # Procesar empresas con acceso
        company_ids = data.get("company_ids", [])
        if isinstance(company_ids, str):
            company_ids = [int(company_ids)] if company_ids else []
        elif isinstance(company_ids, list):
            company_ids = [int(cid) for cid in company_ids if cid]
        
        # Verificar acceso a las empresas
        for cid in company_ids:
            if not check_company_access(current_user, cid):
                return {"success": False, "message": f"No tienes acceso a la empresa con ID {cid}"}
        
        # Crear ubicación
        db_location = Location(
            name=data["name"],
            description=data.get("description"),
            code=data.get("code"),
            parent_id=parent_id,
            location_type=LocationType(data.get("location_type", "AREA")),
            max_capacity=max_capacity,
            shelf_count=shelf_count,
            sort_order=sort_order,
            company_id=company_id,
            is_active=data.get("is_active", True)
        )
        
        db.add(db_location)
        db.flush()  # Para obtener el ID
        
        # Agregar empresas con acceso
        if company_ids:
            companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
            db_location.companies = companies
        
        db.commit()
        
        return {"success": True, "message": "Ubicación creada exitosamente"}
        
    except ValueError as e:
        return {"success": False, "message": f"Error de validación: {str(e)}"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al crear la ubicación: {str(e)}"}


# Reports
@router.get("/reports", response_class=HTMLResponse, name="admin_reports")
async def admin_reports(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de reportes administrativos"""
    # Estadísticas generales
    total_companies = db.query(Company).filter(Company.is_active == True).count()
    total_devices = db.query(Device).filter(Device.is_active == True).count()
    total_users = db.query(User).filter(User.is_active == True).count()
    total_locations = db.query(Location).filter(Location.is_active == True).count()
    
    # Dispositivos por estado
    devices_by_status = {}
    for status in DeviceStatus:
        count = db.query(Device).filter(
            Device.status == status,
            Device.is_active == True
        ).count()
        devices_by_status[status.value] = count
    
    # Ingresos mensuales - calcular suma de costos de todas las empresas
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
    
    # Empresas con más dispositivos
    try:
        companies_with_devices = db.query(
            Company.id,
            Company.name,
            func.count(Device.id).label('device_count')
        ).join(
            Device, Company.id == Device.company_id, isouter=False
        ).filter(
            Company.is_active == True,
            Device.is_active == True
        ).group_by(
            Company.id, Company.name
        ).order_by(
            func.count(Device.id).desc()
        ).limit(10).all()
    except Exception as e:
        # Si hay error en la consulta, usar lista vacía
        companies_with_devices = []
    
    # Ubicaciones con más dispositivos
    try:
        locations_with_devices = db.query(
            Location.id,
            Location.name,
            Location.location_type,
            func.count(Device.id).label('device_count')
        ).join(
            Device, Location.id == Device.location_id, isouter=False
        ).filter(
            Location.is_active == True,
            Device.is_active == True
        ).group_by(
            Location.id, Location.name, Location.location_type
        ).order_by(
            func.count(Device.id).desc()
        ).limit(10).all()
    except Exception as e:
        # Si hay error en la consulta, usar lista vacía
        locations_with_devices = []
    
    stats = {
        'total_companies': total_companies,
        'total_devices': total_devices,
        'total_users': total_users,
        'total_locations': total_locations,
        'monthly_revenue': monthly_revenue,
        'devices_by_status': devices_by_status
    }
    
    return templates.TemplateResponse(
        "admin/reports.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
            "companies_with_devices": companies_with_devices,
            "locations_with_devices": locations_with_devices
        }
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Eliminar un usuario"""
    try:
        # Buscar el usuario
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # No permitir que un usuario se elimine a sí mismo
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
        
        # Si el usuario actual es staff, no puede eliminar otros staff o super admins
        if current_user.role == UserRole.STAFF and user.role in [UserRole.STAFF, UserRole.SUPERADMIN]:
            raise HTTPException(status_code=403, detail="Los usuarios staff no pueden eliminar otros staff o super admins")
        
        # Eliminar el usuario (soft delete)
        user.is_active = False
        user.email = f"deleted_{user.id}_{user.email}"
        
        db.commit()
        
        return {"message": "Usuario eliminado exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Activar o desactivar un usuario"""
    try:
        # Obtener datos del request
        data = await request.json()
        is_active = data.get("is_active")
        
        if is_active is None:
            raise HTTPException(status_code=400, detail="Estado requerido")
        
        # Buscar el usuario
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # No permitir que un usuario cambie su propio estado
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="No puedes cambiar tu propio estado")
        
        # Actualizar el estado
        user.is_active = is_active
        
        db.commit()
        
        return {"message": f"Usuario {'activado' if is_active else 'desactivado'} exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Configuración del sistema
@router.get("/settings", response_class=HTMLResponse, name="admin_settings")
async def settings_page(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de configuración del sistema"""
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Configuración", "url": ""}
    ]
    
    return templates.TemplateResponse("admin/settings.html", {
        "request": request,
        "current_user": current_user,
        "breadcrumbs": breadcrumbs
    })


# ==================== HELP ROUTES ====================

@router.get("/help/superadmin", response_class=HTMLResponse)
async def help_superadmin(
    request: Request,
    current_user: User = Depends(require_superadmin)
):
    """Página de ayuda para Superadmin"""
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Guía de Superadmin", "url": ""}
    ]
    
    return templates.TemplateResponse("admin/help_superadmin.html", {
        "request": request,
        "current_user": current_user,
        "breadcrumbs": breadcrumbs
    })


@router.get("/help/staff", response_class=HTMLResponse)
async def help_staff(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de ayuda para Staff"""
    # Verificar que el usuario sea staff (no superadmin)
    if current_user.role != UserRole.STAFF:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Breadcrumbs
    breadcrumbs = [
        {"title": "Dashboard", "url": "/admin/dashboard"},
        {"title": "Guía de Staff", "url": ""}
    ]
    
    return templates.TemplateResponse("admin/help_staff.html", {
        "request": request,
        "current_user": current_user,
        "breadcrumbs": breadcrumbs
    })