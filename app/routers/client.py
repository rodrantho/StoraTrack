from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, Device, DeviceMovement, Tag, Location, UserRole
from app.auth import get_current_active_user
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Dashboard del cliente"""
    # Solo usuarios de cliente pueden acceder
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    # Estadísticas de dispositivos
    total_devices = db.query(Device).filter(
        Device.company_id == current_user.company_id,
        Device.is_active == True
    ).count()
    
    # Dispositivos por estado
    from app.models import DeviceStatus
    devices_by_status = {}
    for status in DeviceStatus:
        count = db.query(Device).filter(
            Device.company_id == current_user.company_id,
            Device.status == status,
            Device.is_active == True
        ).count()
        devices_by_status[status.value] = count
    
    # Costo total acumulado hasta hoy
    total_cost = calculate_total_cost_to_date(db, current_user.company_id)
    
    # Movimientos recientes
    recent_movements = db.query(DeviceMovement).join(Device).filter(
        Device.company_id == current_user.company_id,
        Device.is_active == True
    ).order_by(DeviceMovement.created_at.desc()).limit(10).all()
    
    # Dispositivos ingresados recientemente
    recent_devices = db.query(Device).filter(
        Device.company_id == current_user.company_id,
        Device.is_active == True
    ).order_by(Device.fecha_ingreso.desc()).limit(5).all()
    
    return templates.TemplateResponse("client/dashboard.html", {
        "request": request,
        "current_user": current_user,
        "total_devices": total_devices,
        "devices_by_status": devices_by_status,
        "total_cost": total_cost,
        "recent_movements": recent_movements,
        "recent_devices": recent_devices
    })

@router.get("/devices", response_class=HTMLResponse)
async def list_devices(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    location_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Listar dispositivos del cliente"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    page_size = settings.default_page_size
    offset = (page - 1) * page_size
    
    # Query base
    query = db.query(Device).filter(
        Device.company_id == current_user.company_id,
        Device.is_active == True
    )
    
    # Filtros
    if search:
        query = query.filter(
            or_(
                Device.name.ilike(f"%{search}%"),
                Device.serial_number.ilike(f"%{search}%"),
                Device.model.ilike(f"%{search}%"),
                Device.brand.ilike(f"%{search}%")
            )
        )
    
    if status:
        from app.models import DeviceStatus
        try:
            device_status = DeviceStatus(status)
            query = query.filter(Device.status == device_status)
        except ValueError:
            pass
    
    if location_id:
        query = query.filter(Device.location_id == location_id)
    
    if tag_id:
        query = query.join(Device.tags).filter(Tag.id == tag_id)
    
    # Obtener resultados
    devices = query.offset(offset).limit(page_size).all()
    total = query.count()
    pages = (total + page_size - 1) // page_size
    
    # Datos para filtros
    locations = db.query(Location).filter(
        Location.company_id == current_user.company_id,
        Location.is_active == True
    ).all()
    
    tags = db.query(Tag).filter(
        Tag.company_id == current_user.company_id,
        Tag.is_active == True
    ).all()
    
    from app.models import DeviceStatus
    
    return templates.TemplateResponse("client/devices/list.html", {
        "request": request,
        "current_user": current_user,
        "devices": devices,
        "locations": locations,
        "tags": tags,
        "device_statuses": DeviceStatus,
        "filters": {
            "search": search,
            "status": status,
            "location_id": location_id,
            "tag_id": tag_id
        },
        "page": page,
        "pages": pages,
        "total": total
    })

@router.get("/devices/{device_id}", response_class=HTMLResponse)
async def view_device(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ver detalle de dispositivo"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.company_id == current_user.company_id,
        Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Calcular costo actual
    current_cost = calculate_device_cost(device, datetime.utcnow())
    
    # Historial de movimientos
    movements = db.query(DeviceMovement).filter(
        DeviceMovement.device_id == device_id
    ).order_by(DeviceMovement.created_at.desc()).all()
    
    return templates.TemplateResponse("client/devices/view.html", {
        "request": request,
        "current_user": current_user,
        "device": device,
        "current_cost": current_cost,
        "movements": movements
    })

@router.get("/devices/{device_id}/qr")
async def device_qr_code(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generar código QR del dispositivo"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.company_id == current_user.company_id,
        Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Generar QR
    import qrcode
    from io import BytesIO
    
    qr_data = f"StoraTrack-{device.id}-{device.name}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a bytes
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return Response(
        content=img_buffer.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=device_{device_id}_qr.png"}
    )

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Página de reportes"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    # Reportes mensuales disponibles
    from app.models import MonthlyReport
    monthly_reports = db.query(MonthlyReport).filter(
        MonthlyReport.company_id == current_user.company_id,
        MonthlyReport.is_closed == True
    ).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()
    
    # Costo actual del mes
    now = datetime.utcnow()
    current_month_cost = calculate_monthly_cost(db, current_user.company_id, now.year, now.month)
    
    return templates.TemplateResponse("client/reports.html", {
        "request": request,
        "current_user": current_user,
        "monthly_reports": monthly_reports,
        "current_month_cost": current_month_cost,
        "current_year": now.year,
        "current_month": now.month
    })

@router.get("/reports/current")
async def download_current_report(
    format: str = Query("pdf", regex="^(pdf|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar reporte actual"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    # Generar reporte hasta la fecha actual
    now = datetime.utcnow()
    
    if format == "pdf":
        pdf_content = generate_pdf_report(db, current_user.company_id, now.year, now.month, now)
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=reporte_{now.year}_{now.month:02d}.pdf"}
        )
    else:
        csv_content = generate_csv_report(db, current_user.company_id, now.year, now.month, now)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=reporte_{now.year}_{now.month:02d}.csv"}
        )

# Funciones auxiliares
def calculate_device_cost(device: Device, fecha_hasta: datetime) -> dict:
    """Calcular costo de un dispositivo hasta una fecha"""
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
        "dias": dias,
        "costo_base": costo_base,
        "costo_diario": costo_diario,
        "subtotal": subtotal,
        "iva_amount": iva_amount,
        "total": total
    }

def calculate_total_cost_to_date(db: Session, company_id: int) -> float:
    """Calcular costo total de todos los dispositivos hasta la fecha"""
    devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).all()
    
    total = 0.0
    for device in devices:
        cost_info = calculate_device_cost(device, datetime.utcnow())
        total += cost_info["total"]
    
    return total

def calculate_monthly_cost(db: Session, company_id: int, year: int, month: int) -> float:
    """Calcular costo mensual"""
    from calendar import monthrange
    
    # Último día del mes
    last_day = monthrange(year, month)[1]
    fecha_hasta = datetime(year, month, last_day, 23, 59, 59)
    
    devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.fecha_ingreso <= fecha_hasta,
        Device.is_active == True
    ).all()
    
    total = 0.0
    for device in devices:
        cost_info = calculate_device_cost(device, fecha_hasta)
        total += cost_info["total"]
    
    return total

def generate_pdf_report(db: Session, company_id: int, year: int, month: int, fecha_hasta: datetime) -> bytes:
    """Generar reporte PDF"""
    # Implementación básica - se puede mejorar con WeasyPrint
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Título
    p.drawString(100, 750, f"Reporte de Almacenamiento - {month:02d}/{year}")
    
    # Obtener dispositivos y costos
    devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.fecha_ingreso <= fecha_hasta,
        Device.is_active == True
    ).all()
    
    y = 700
    total_general = 0.0
    
    for device in devices:
        cost_info = calculate_device_cost(device, fecha_hasta)
        p.drawString(100, y, f"{device.name} - ${cost_info['total']:.2f}")
        total_general += cost_info['total']
        y -= 20
        
        if y < 100:
            p.showPage()
            y = 750
    
    # Total
    p.drawString(100, y - 20, f"TOTAL: ${total_general:.2f}")
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def generate_csv_report(db: Session, company_id: int, year: int, month: int, fecha_hasta: datetime) -> str:
    """Generar reporte CSV"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Dispositivo', 'Serie', 'Fecha Ingreso', 'Días', 
        'Costo Base', 'Costo Diario', 'Subtotal', 'IVA', 'Total'
    ])
    
    # Obtener dispositivos
    devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.fecha_ingreso <= fecha_hasta,
        Device.is_active == True
    ).all()
    
    total_general = 0.0
    
    for device in devices:
        cost_info = calculate_device_cost(device, fecha_hasta)
        writer.writerow([
            device.name,
            device.serial_number or '',
            device.fecha_ingreso.strftime('%d/%m/%Y'),
            cost_info['dias'],
            cost_info['costo_base'],
            cost_info['costo_diario'],
            cost_info['subtotal'],
            cost_info['iva_amount'],
            cost_info['total']
        ])
        total_general += cost_info['total']
    
    # Total
    writer.writerow(['', '', '', '', '', '', '', 'TOTAL:', total_general])
    
    return output.getvalue()