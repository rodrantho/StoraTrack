from fastapi import APIRouter, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User, Company, Device, Location, Tag, UserRole
from app.schemas import (
    CompanyCreate, CompanyUpdate, UserCreate, UserUpdate,
    LocationCreate, LocationUpdate, TagCreate, TagUpdate,
    DeviceCreate, DeviceUpdate
)
from app.auth import (
    require_admin_or_staff, 
    require_superadmin,
    get_current_active_user,
    get_password_hash
)
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Dashboard
@router.get("/dashboard", response_class=HTMLResponse)
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
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "current_user": current_user,
        "total_companies": total_companies,
        "total_devices": total_devices,
        "total_users": total_users,
        "devices_by_status": devices_by_status,
        "recent_companies": recent_companies
    })

# Gestión de empresas
@router.get("/companies", response_class=HTMLResponse)
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
    
    return templates.TemplateResponse("admin/companies/list.html", {
        "request": request,
        "current_user": current_user,
        "companies": companies,
        "page": page,
        "pages": pages,
        "total": total
    })

@router.get("/companies/new", response_class=HTMLResponse)
async def new_company_form(
    request: Request,
    current_user: User = Depends(require_superadmin)
):
    """Formulario nueva empresa"""
    return templates.TemplateResponse("admin/companies/form.html", {
        "request": request,
        "current_user": current_user,
        "company": None,
        "action": "create"
    })

@router.post("/companies/new")
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
    current_user: User = Depends(require_superadmin)
):
    """Crear empresa"""
    # Verificar que no exista el RUT
    existing = db.query(Company).filter(Company.rut_id == rut_id).first()
    if existing:
        return templates.TemplateResponse("admin/companies/form.html", {
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

@router.get("/companies/{company_id}", response_class=HTMLResponse)
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
    
    return templates.TemplateResponse("admin/companies/view.html", {
        "request": request,
        "current_user": current_user,
        "company": company,
        "total_devices": total_devices,
        "total_users": total_users
    })

@router.get("/companies/{company_id}/edit", response_class=HTMLResponse)
async def edit_company_form(
    request: Request,
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Formulario editar empresa"""
    company = db.query(Company).filter(
        Company.id == company_id,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return templates.TemplateResponse("admin/companies/form.html", {
        "request": request,
        "current_user": current_user,
        "company": company,
        "action": "edit"
    })

@router.post("/companies/{company_id}/edit")
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
    current_user: User = Depends(require_superadmin)
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
    
    from datetime import datetime
    company.updated_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(url=f"/admin/companies/{company_id}", status_code=302)

# Gestión de usuarios
@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    page: int = 1,
    company_id: Optional[int] = None,
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
    
    return templates.TemplateResponse("admin/users/list.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "companies": companies,
        "selected_company_id": company_id,
        "page": page,
        "pages": pages,
        "total": total
    })

@router.get("/users/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Formulario nuevo usuario"""
    companies = db.query(Company).filter(Company.is_active == True).all()
    
    return templates.TemplateResponse("admin/users/form.html", {
        "request": request,
        "current_user": current_user,
        "user": None,
        "companies": companies,
        "action": "create",
        "user_roles": UserRole
    })

@router.post("/users/new")
async def create_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    company_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_staff)
):
    """Crear usuario"""
    # Verificar que no exista el email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        companies = db.query(Company).filter(Company.is_active == True).all()
        return templates.TemplateResponse("admin/users/form.html", {
            "request": request,
            "current_user": current_user,
            "user": None,
            "companies": companies,
            "action": "create",
            "user_roles": UserRole,
            "error": "Ya existe un usuario con ese email"
        })
    
    # Validar rol
    try:
        user_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rol inválido")
    
    # Solo superadmin puede crear otros superadmin
    if user_role == UserRole.SUPERADMIN and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear superadministradores")
    
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=user_role,
        company_id=company_id if user_role != UserRole.SUPERADMIN else None
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return RedirectResponse(url="/admin/users", status_code=302)

# Etiquetas
@router.get("/labels", response_class=HTMLResponse)
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
@router.get("/devices", response_class=HTMLResponse)
async def devices_page(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de gestión de dispositivos"""
    return templates.TemplateResponse(
        "admin/devices.html",
        {"request": request, "current_user": current_user}
    )

# Ubicaciones
@router.get("/locations", response_class=HTMLResponse)
async def locations_page(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de gestión de ubicaciones"""
    return templates.TemplateResponse(
        "admin/locations.html",
        {"request": request, "current_user": current_user}
    )

# Tags
@router.get("/tags", response_class=HTMLResponse)
async def tags_page(
    request: Request,
    current_user: User = Depends(require_admin_or_staff)
):
    """Página de gestión de tags"""
    return templates.TemplateResponse(
        "admin/tags.html",
        {"request": request, "current_user": current_user}
    )