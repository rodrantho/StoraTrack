from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
import io
from ..database import get_db
from ..models import Device, Company, User
from ..services.cost_calculator import CostCalculator
from ..services.report_generator import ReportGenerator
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/cost-reports", tags=["cost-reports"])

@router.get("/device/{device_id}/cost")
async def get_device_cost(
    device_id: int,
    calculation_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el cálculo de costo de un dispositivo específico"""
    
    # Obtener dispositivo
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Verificar permisos
    if current_user.role == 'client' and device.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este dispositivo")
    
    # Parsear fecha si se proporciona
    calc_date = None
    if calculation_date:
        try:
            calc_date = datetime.strptime(calculation_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Calcular costo
    calculator = CostCalculator(db)
    cost_data = calculator.calculate_device_cost(device, calc_date)
    
    return {
        "success": True,
        "data": cost_data
    }

@router.get("/device/{device_id}/report")
async def get_device_cost_report(
    device_id: int,
    format: str = "pdf",
    calculation_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Genera reporte de costo de un dispositivo en PDF o CSV"""
    
    # Validar formato
    if format not in ["pdf", "csv"]:
        raise HTTPException(status_code=400, detail="Formato debe ser 'pdf' o 'csv'")
    
    # Obtener dispositivo
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Verificar permisos
    if current_user.role == 'client' and device.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este dispositivo")
    
    # Parsear fecha si se proporciona
    calc_date = None
    if calculation_date:
        try:
            calc_date = datetime.strptime(calculation_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    # Generar reporte
    generator = ReportGenerator(db)
    
    if format == "pdf":
        pdf_content = generator.generate_device_cost_report_pdf(device, calc_date)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=costo-{device.name}-{datetime.now().strftime('%Y%m%d')}.pdf"}
        )
    
    else:  # CSV
        csv_content = generator.generate_device_cost_report_csv(device, calc_date)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=costo-{device.name}-{datetime.now().strftime('%Y%m%d')}.csv"}
        )

@router.get("/company/{company_id}/monthly")
async def get_company_monthly_cost(
    company_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el cálculo de costo mensual de una empresa"""
    
    # Obtener empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar permisos
    if current_user.role == 'client' and company.id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta empresa")
    
    # Validar fecha
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mes debe estar entre 1 y 12")
    
    if year < 2020 or year > datetime.now().year + 1:
        raise HTTPException(status_code=400, detail="Año inválido")
    
    # Calcular costo mensual
    calculator = CostCalculator(db)
    monthly_data = calculator.calculate_company_monthly_cost(company, year, month)
    
    return {
        "success": True,
        "data": monthly_data
    }

@router.get("/company/{company_id}/monthly-report")
async def get_company_monthly_report(
    company_id: int,
    year: int,
    month: int,
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Genera reporte mensual de una empresa en PDF o CSV"""
    
    # Validar formato
    if format not in ["pdf", "csv"]:
        raise HTTPException(status_code=400, detail="Formato debe ser 'pdf' o 'csv'")
    
    # Obtener empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar permisos
    if current_user.role == 'client' and company.id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta empresa")
    
    # Validar fecha
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mes debe estar entre 1 y 12")
    
    if year < 2020 or year > datetime.now().year + 1:
        raise HTTPException(status_code=400, detail="Año inválido")
    
    # Generar reporte
    generator = ReportGenerator(db)
    
    if format == "pdf":
        pdf_content = generator.generate_company_monthly_report_pdf(company, year, month)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=reporte-mensual-{company.name}-{year}-{month:02d}.pdf"}
        )
    
    else:  # CSV
        csv_content = generator.generate_company_monthly_report_csv(company, year, month)
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=reporte-mensual-{company.name}-{year}-{month:02d}.csv"}
        )

@router.get("/company/{company_id}/summary")
async def get_company_cost_summary(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene resumen de costos de una empresa"""
    
    # Obtener empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar permisos
    if current_user.role == 'client' and company.id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta empresa")
    
    # Obtener resumen
    calculator = CostCalculator(db)
    summary = calculator.get_company_cost_summary(company)
    
    return {
        "success": True,
        "data": summary
    }

@router.get("/company/{company_id}/historical")
async def get_company_historical_costs(
    company_id: int,
    months_back: int = 12,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene costos históricos de una empresa"""
    
    # Obtener empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar permisos
    if current_user.role == 'client' and company.id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta empresa")
    
    # Validar parámetros
    if months_back < 1 or months_back > 24:
        raise HTTPException(status_code=400, detail="months_back debe estar entre 1 y 24")
    
    # Obtener histórico
    calculator = CostCalculator(db)
    historical = calculator.calculate_historical_costs(company, months_back)
    
    return {
        "success": True,
        "data": historical
    }

@router.get("/company/{company_id}/breakdown")
async def get_company_cost_breakdown(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene desglose de costos por estado de dispositivos"""
    
    # Obtener empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Verificar permisos
    if current_user.role == 'client' and company.id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver esta empresa")
    
    # Obtener desglose
    calculator = CostCalculator(db)
    breakdown = calculator.get_cost_breakdown_by_status(company)
    
    return {
        "success": True,
        "data": breakdown
    }

@router.get("/devices/export")
async def export_devices_list(
    format: str = "csv",
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["superadmin", "staff"]))
):
    """Exporta lista de dispositivos con costos (solo admin)"""
    
    # Validar formato
    if format not in ["csv"]:
        raise HTTPException(status_code=400, detail="Formato debe ser 'csv'")
    
    # Construir query
    query = db.query(Device)
    
    if company_id:
        query = query.filter(Device.company_id == company_id)
    
    if status:
        query = query.filter(Device.status == status)
    
    devices = query.all()
    
    # Generar reporte
    generator = ReportGenerator(db)
    csv_content = generator.generate_devices_list_csv(devices)
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=equipos-{datetime.now().strftime('%Y%m%d')}.csv"}
    )

# Rutas adicionales para compatibilidad con las plantillas existentes
@router.get("/devices/{device_id}/cost")
async def get_device_cost_legacy(
    device_id: int,
    calculation_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ruta legacy para compatibilidad con plantillas"""
    return await get_device_cost(device_id, calculation_date, db, current_user)

@router.get("/devices/{device_id}/cost-report")
async def get_device_cost_report_legacy(
    device_id: int,
    format: str = "pdf",
    calculation_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ruta legacy para compatibilidad con plantillas"""
    return await get_device_cost_report(device_id, format, calculation_date, db, current_user)