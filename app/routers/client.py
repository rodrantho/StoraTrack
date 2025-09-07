from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User, Device, DeviceMovement, Tag, Location, UserRole, DeviceStatus
from app.auth import get_current_active_user
from app.config import settings
from app.utils.datetime_utils import now_local

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse, name="client_dashboard")
async def client_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Dashboard del cliente"""
    # Verificar que el usuario sea un cliente
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Verificar que el usuario tenga una empresa asignada
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    try:
        # Estadísticas básicas
        total_devices = db.query(Device).filter(
            Device.company_id == current_user.company_id,
            Device.is_active == True
        ).count()
        
        # Dispositivos por estado
        devices_by_status = {}
        for status in DeviceStatus:
            count = db.query(Device).filter(
                Device.company_id == current_user.company_id,
                Device.is_active == True,
                Device.status == status
            ).count()
            devices_by_status[status.value] = count
        
        # Costo total estimado (simplificado)
        total_cost = total_devices * 1000.0  # Costo base estimado
        
        stats = {
            'total_devices': total_devices,
            'devices_by_status': devices_by_status,
            'total_cost': total_cost,
            'stored_devices': devices_by_status.get('almacenado', 0),
            'monthly_cost': total_cost * 0.1,  # 10% del costo total como costo mensual
            'total_accumulated_cost': total_cost * 1.5  # Costo acumulado estimado
        }
        
        # Movimientos recientes
        recent_movements = db.query(DeviceMovement).join(Device).filter(
            Device.company_id == current_user.company_id
        ).order_by(DeviceMovement.created_at.desc()).limit(5).all()
        
        # Dispositivos recientes
        recent_devices = db.query(Device).filter(
            Device.company_id == current_user.company_id,
            Device.is_active == True
        ).order_by(Device.created_at.desc()).limit(5).all()
        
    except Exception as e:
        # En caso de error, usar valores por defecto
        print(f"ERROR en client_dashboard: {str(e)}")
        stats = {
            'total_devices': 0,
            'devices_by_status': {},
            'total_cost': 0.0,
            'stored_devices': 0,
            'monthly_cost': 0.0,
            'total_accumulated_cost': 0.0
        }
        recent_movements = []
        recent_devices = []
    
    return templates.TemplateResponse(
        "client/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
            "recent_movements": recent_movements,
            "recent_devices": recent_devices
        }
    )

@router.get("/devices", response_class=HTMLResponse, name="client_devices")
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
    
    return templates.TemplateResponse("client/devices.html", {
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

@router.get("/devices/{device_id}", response_class=HTMLResponse, name="client_device_detail")
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
    current_cost = calculate_device_cost(device, now_local())
    
    # Historial de movimientos
    movements = db.query(DeviceMovement).filter(
        DeviceMovement.device_id == device_id
    ).order_by(DeviceMovement.created_at.desc()).all()
    
    return templates.TemplateResponse("client/device_detail.html", {
        "request": request,
        "current_user": current_user,
        "device": device,
        "current_cost": current_cost,
        "movements": movements
    })

@router.get("/devices/{device_id}/qr", name="client_device_qr")
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

@router.get("/reports", response_class=HTMLResponse, name="client_reports")
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
    now = now_local()
    current_month_cost = calculate_monthly_cost(db, current_user.company_id, now.year, now.month)
    
    # Estadísticas actuales para el resumen
    total_devices = db.query(Device).filter(
        Device.company_id == current_user.company_id,
        Device.is_active == True
    ).count()
    stored_devices = db.query(Device).filter(
        Device.company_id == current_user.company_id,
        Device.is_active == True,
        Device.status == DeviceStatus.ALMACENADO
    ).count()
    
    # Costo total acumulado de todos los reportes cerrados
    total_accumulated = db.query(func.sum(MonthlyReport.total_cost)).filter(
        MonthlyReport.company_id == current_user.company_id,
        MonthlyReport.is_closed == True
    ).scalar() or 0.0
    
    current_stats = {
        'total_devices': total_devices,
        'stored_devices': stored_devices,
        'monthly_cost': current_month_cost,
        'total_accumulated': total_accumulated,
        'base_costs': current_month_cost * 0.8,  # Estimación de costos base
        'storage_costs': current_month_cost * 0.2,  # Estimación de costos de almacenamiento
        'subtotal': current_month_cost,
        'iva_amount': 0.0,  # Se calculará según la configuración de la empresa
        'total': current_month_cost
    }
    
    # Información del período actual
    from calendar import monthrange
    days_in_month = monthrange(now.year, now.month)[1]
    current_period = {
        'start': f"{now.year}-{now.month:02d}-01",
        'end': f"{now.year}-{now.month:02d}-{days_in_month}",
        'days_elapsed': now.day
    }
    
    # Obtener información de la empresa
    from app.models import Company
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    return templates.TemplateResponse("client/reports.html", {
        "request": request,
        "current_user": current_user,
        "monthly_reports": monthly_reports,
        "current_month_cost": current_month_cost,
        "current_stats": current_stats,
        "current_period": current_period,
        "company": company,
        "current_year": now.year,
        "current_month": now.month
    })

@router.get("/reports/current", name="client_reports_current")
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
    now = now_local()
    
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

@router.get("/reports/current/{format}", name="client_reports_current_format")
async def download_current_report_format(
    format: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar reporte actual"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    # Generar reporte hasta la fecha actual
    now = now_local()
    
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

@router.get("/api/current-cost", name="client_api_current_cost")
async def get_current_cost(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener costo actual de la empresa"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    try:
        total_cost = calculate_total_cost_to_date(db, current_user.company_id)
        return {"current_cost": total_cost}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular costo: {str(e)}")

@router.get("/reports/{report_id}/{format}", name="client_reports_download")
async def download_report(
    report_id: str,
    format: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Descargar reporte específico"""
    if current_user.role != UserRole.CLIENT_USER:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    
    try:
        # Parsear el report_id para obtener año y mes
        year, month = map(int, report_id.split('-'))
        
        # Generar reporte hasta el último día del mes
        from calendar import monthrange
        last_day = monthrange(year, month)[1]
        fecha_hasta = datetime(year, month, last_day, 23, 59, 59)
        
        if format == "pdf":
            pdf_content = generate_pdf_report(db, current_user.company_id, year, month, fecha_hasta)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=reporte_{year}_{month:02d}.pdf"}
            )
        else:
            csv_content = generate_csv_report(db, current_user.company_id, year, month, fecha_hasta)
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=reporte_{year}_{month:02d}.csv"}
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de reporte inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar reporte: {str(e)}")

# Funciones auxiliares
def calculate_device_cost(device: Device, fecha_hasta: datetime) -> dict:
    """Calcular costo de un dispositivo hasta una fecha"""
    try:
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
        
        return {
            "dias": dias,
            "costo_base": costo_base,
            "costo_diario": costo_diario,
            "subtotal": subtotal,
            "iva_amount": iva_amount,
            "total": total
        }
    except Exception as e:
        print(f"Error in calculate_device_cost for device {device.id}: {e}")
        return {
            "dias": 0,
            "costo_base": 0.0,
            "costo_diario": 0.0,
            "subtotal": 0.0,
            "iva_amount": 0.0,
            "total": 0.0
        }

def calculate_total_cost_to_date(db: Session, company_id: int) -> float:
    """Calcular costo total de todos los dispositivos hasta la fecha"""
    devices = db.query(Device).filter(
        Device.company_id == company_id,
        Device.is_active == True
    ).all()
    
    total = 0.0
    for device in devices:
        try:
            cost_info = calculate_device_cost(device, datetime.utcnow())
            total += cost_info["total"]
        except Exception as e:
            print(f"Error calculating cost for device {device.id}: {e}")
            continue
    
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