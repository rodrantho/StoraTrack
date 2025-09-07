from datetime import datetime, date
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from ..models import Device, Company, DeviceMovement

class CostCalculator:
    """Servicio para calcular costos de almacenamiento de equipos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_device_cost(self, device: Device, calculation_date: Optional[date] = None) -> Dict[str, Any]:
        """Calcula el costo total de un equipo hasta una fecha específica"""
        if calculation_date is None:
            calculation_date = date.today()
        
        # Obtener información básica
        entry_date = device.entry_date.date() if hasattr(device.entry_date, 'date') else device.entry_date
        days_stored = (calculation_date - entry_date).days
        
        # Calcular costos base
        base_cost = Decimal(str(device.base_cost))
        daily_cost = Decimal(str(device.daily_cost))
        storage_cost = daily_cost * days_stored
        
        # Subtotal sin IVA
        subtotal = base_cost + storage_cost
        
        # Calcular IVA si aplica
        iva_percent = Decimal(str(device.company.iva_percent or 0))
        iva_amount = Decimal('0')
        
        if device.company.apply_iva and iva_percent > 0:
            iva_amount = (subtotal * iva_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Total final
        total_cost = subtotal + iva_amount
        
        return {
            'device_id': device.id,
            'device_name': device.name,
            'company_name': device.company.name,
            'currency': device.company.currency,
            'entry_date': entry_date.isoformat(),
            'calculation_date': calculation_date.isoformat(),
            'days_stored': days_stored,
            'base_cost': float(base_cost),
            'daily_cost': float(daily_cost),
            'storage_cost': float(storage_cost),
            'subtotal': float(subtotal),
            'iva_percent': float(iva_percent),
            'iva_amount': float(iva_amount),
            'total_cost': float(total_cost),
            'apply_iva': device.company.apply_iva,
            'status': device.status,
            'location': device.location.name if device.location else None
        }
    
    def calculate_company_monthly_cost(self, company: Company, year: int, month: int) -> Dict[str, Any]:
        """Calcula el costo mensual total de una empresa"""
        from calendar import monthrange
        
        # Fechas del mes
        start_date = date(year, month, 1)
        last_day = monthrange(year, month)[1]
        end_date = date(year, month, last_day)
        
        # Obtener dispositivos activos durante el mes
        devices = self.db.query(Device).filter(
            Device.company_id == company.id,
            Device.entry_date <= end_date
        ).all()
        
        total_devices = 0
        total_cost = Decimal('0')
        device_costs = []
        
        for device in devices:
            # Verificar si el dispositivo estuvo activo durante el mes
            device_entry = device.entry_date.date() if hasattr(device.entry_date, 'date') else device.entry_date
            
            # Verificar si fue retirado antes del mes
            last_movement = self.db.query(DeviceMovement).filter(
                DeviceMovement.device_id == device.id,
                DeviceMovement.to_status == 'RETIRADO',
                DeviceMovement.created_at <= end_date
            ).order_by(DeviceMovement.created_at.desc()).first()
            
            if last_movement:
                retirement_date = last_movement.created_at.date()
                if retirement_date < start_date:
                    continue  # Retirado antes del mes
            
            # Calcular costo para este dispositivo
            device_cost = self.calculate_device_cost(device, end_date)
            device_costs.append(device_cost)
            total_devices += 1
            total_cost += Decimal(str(device_cost['total_cost']))
        
        return {
            'company_id': company.id,
            'company_name': company.name,
            'currency': company.currency,
            'year': year,
            'month': month,
            'month_name': start_date.strftime('%B'),
            'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            'total_devices': total_devices,
            'total_cost': float(total_cost),
            'devices': device_costs,
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_device_cost_range(self, device: Device, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calcula el costo de un equipo en un rango de fechas específico"""
        device_entry = device.entry_date.date() if hasattr(device.entry_date, 'date') else device.entry_date
        
        # Ajustar fechas si es necesario
        actual_start = max(start_date, device_entry)
        actual_end = end_date
        
        # Verificar si fue retirado durante el período
        last_movement = self.db.query(DeviceMovement).filter(
            DeviceMovement.device_id == device.id,
            DeviceMovement.to_status == 'RETIRADO',
            DeviceMovement.created_at <= end_date
        ).order_by(DeviceMovement.created_at.desc()).first()
        
        if last_movement:
            retirement_date = last_movement.created_at.date()
            actual_end = min(actual_end, retirement_date)
        
        # Calcular días en el período
        if actual_end < actual_start:
            days_in_period = 0
        else:
            days_in_period = (actual_end - actual_start).days + 1
        
        # Calcular costos
        base_cost = Decimal(str(device.base_cost))
        daily_cost = Decimal(str(device.daily_cost))
        period_storage_cost = daily_cost * days_in_period
        
        # Para el costo base, solo se cobra una vez por dispositivo
        # Si el período incluye la fecha de entrada, se incluye el costo base
        include_base_cost = actual_start == device_entry
        period_base_cost = base_cost if include_base_cost else Decimal('0')
        
        # Subtotal
        subtotal = period_base_cost + period_storage_cost
        
        # IVA
        iva_percent = Decimal(str(device.company.iva_percent or 0))
        iva_amount = Decimal('0')
        
        if device.company.apply_iva and iva_percent > 0:
            iva_amount = (subtotal * iva_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        total_cost = subtotal + iva_amount
        
        return {
            'device_id': device.id,
            'device_name': device.name,
            'period_start': actual_start.isoformat(),
            'period_end': actual_end.isoformat(),
            'days_in_period': days_in_period,
            'include_base_cost': include_base_cost,
            'period_base_cost': float(period_base_cost),
            'daily_cost': float(daily_cost),
            'period_storage_cost': float(period_storage_cost),
            'subtotal': float(subtotal),
            'iva_percent': float(iva_percent),
            'iva_amount': float(iva_amount),
            'total_cost': float(total_cost)
        }
    
    def get_company_cost_summary(self, company: Company) -> Dict[str, Any]:
        """Obtiene un resumen de costos de la empresa"""
        # Dispositivos activos (no retirados)
        active_devices = self.db.query(Device).filter(
            Device.company_id == company.id,
            Device.status != 'RETIRADO'
        ).all()
        
        total_active = len(active_devices)
        current_monthly_cost = Decimal('0')
        total_accumulated_cost = Decimal('0')
        
        for device in active_devices:
            device_cost = self.calculate_device_cost(device)
            current_monthly_cost += Decimal(str(device_cost['storage_cost']))
            total_accumulated_cost += Decimal(str(device_cost['total_cost']))
        
        # Todos los dispositivos para estadísticas generales
        all_devices = self.db.query(Device).filter(
            Device.company_id == company.id
        ).all()
        
        total_devices = len(all_devices)
        stored_devices = len([d for d in all_devices if d.status == 'ALMACENADO'])
        
        return {
            'company_id': company.id,
            'company_name': company.name,
            'currency': company.currency,
            'total_devices': total_devices,
            'active_devices': total_active,
            'stored_devices': stored_devices,
            'current_monthly_cost': float(current_monthly_cost),
            'total_accumulated_cost': float(total_accumulated_cost),
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_historical_costs(self, company: Company, months_back: int = 12) -> list:
        """Calcula costos históricos de los últimos N meses"""
        from dateutil.relativedelta import relativedelta
        
        results = []
        current_date = date.today()
        
        for i in range(months_back):
            target_date = current_date - relativedelta(months=i)
            year = target_date.year
            month = target_date.month
            
            monthly_cost = self.calculate_company_monthly_cost(company, year, month)
            results.append(monthly_cost)
        
        return results
    
    def get_cost_breakdown_by_status(self, company: Company) -> Dict[str, Any]:
        """Obtiene desglose de costos por estado de dispositivos"""
        devices = self.db.query(Device).filter(
            Device.company_id == company.id
        ).all()
        
        breakdown = {
            'INGRESADO': {'count': 0, 'total_cost': 0},
            'ESPERANDO_RECIBIR': {'count': 0, 'total_cost': 0},
            'ALMACENADO': {'count': 0, 'total_cost': 0},
            'ENVIADO': {'count': 0, 'total_cost': 0},
            'RETIRADO': {'count': 0, 'total_cost': 0}
        }
        
        for device in devices:
            status = device.status
            if status in breakdown:
                breakdown[status]['count'] += 1
                if status != 'RETIRADO':  # No calcular costo para retirados
                    device_cost = self.calculate_device_cost(device)
                    breakdown[status]['total_cost'] += device_cost['total_cost']
        
        return {
            'company_id': company.id,
            'company_name': company.name,
            'currency': company.currency,
            'breakdown': breakdown,
            'generated_at': datetime.now().isoformat()
        }