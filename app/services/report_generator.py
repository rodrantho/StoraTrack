import io
import csv
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from sqlalchemy.orm import Session
from .cost_calculator import CostCalculator
from ..models.device import Device
from ..models.company import Company

class ReportGenerator:
    """Servicio para generar reportes en PDF y CSV"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cost_calculator = CostCalculator(db)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para los reportes"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_device_cost_report_pdf(self, device: Device, calculation_date: Optional[date] = None) -> bytes:
        """Genera reporte PDF de costo de un dispositivo específico"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Calcular costos
        cost_data = self.cost_calculator.calculate_device_cost(device, calculation_date)
        
        # Contenido del reporte
        story = []
        
        # Título
        title = Paragraph("Reporte de Costo de Equipo", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Información de la empresa
        company_info = [
            ['Empresa:', device.company.name],
            ['RUT/ID:', device.company.rut_id or 'N/A'],
            ['Moneda:', device.company.currency],
            ['Fecha de generación:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        company_table = Table(company_info, colWidths=[2*inch, 4*inch])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # Información del equipo
        story.append(Paragraph("Información del Equipo", self.styles['CustomHeading']))
        
        device_info = [
            ['Nombre:', device.name],
            ['Número de Serie:', device.serial_number or 'N/A'],
            ['Marca:', device.brand or 'N/A'],
            ['Modelo:', device.model or 'N/A'],
            ['Estado:', device.status.replace('_', ' ').title()],
            ['Ubicación:', device.location.name if device.location else 'Sin ubicación'],
            ['Fecha de Ingreso:', cost_data['entry_date']],
            ['Fecha de Cálculo:', cost_data['calculation_date']]
        ]
        
        device_table = Table(device_info, colWidths=[2*inch, 4*inch])
        device_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        
        story.append(device_table)
        story.append(Spacer(1, 20))
        
        # Desglose de costos
        story.append(Paragraph("Desglose de Costos", self.styles['CustomHeading']))
        
        cost_breakdown = [
            ['Concepto', 'Cantidad', 'Precio Unitario', 'Total'],
            ['Costo Base', '1', f"{cost_data['currency']} {cost_data['base_cost']:.2f}", f"{cost_data['currency']} {cost_data['base_cost']:.2f}"],
            ['Almacenamiento', f"{cost_data['days_stored']} días", f"{cost_data['currency']} {cost_data['daily_cost']:.2f}", f"{cost_data['currency']} {cost_data['storage_cost']:.2f}"],
            ['', '', 'Subtotal:', f"{cost_data['currency']} {cost_data['subtotal']:.2f}"]
        ]
        
        if cost_data['apply_iva'] and cost_data['iva_amount'] > 0:
            cost_breakdown.append(['', '', f"IVA ({cost_data['iva_percent']:.0f}%):", f"{cost_data['currency']} {cost_data['iva_amount']:.2f}"])
        
        cost_breakdown.append(['', '', 'TOTAL:', f"{cost_data['currency']} {cost_data['total_cost']:.2f}"])
        
        cost_table = Table(cost_breakdown, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(cost_table)
        
        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_company_monthly_report_pdf(self, company: Company, year: int, month: int) -> bytes:
        """Genera reporte PDF mensual de una empresa"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Calcular costos mensuales
        monthly_data = self.cost_calculator.calculate_company_monthly_cost(company, year, month)
        
        story = []
        
        # Título
        title = Paragraph(f"Reporte Mensual - {monthly_data['month_name']} {year}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Información de la empresa
        company_info = [
            ['Empresa:', company.name],
            ['RUT/ID:', company.rut_id or 'N/A'],
            ['Período:', monthly_data['period']],
            ['Moneda:', company.currency],
            ['Fecha de generación:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        company_table = Table(company_info, colWidths=[2*inch, 4*inch])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(company_table)
        story.append(Spacer(1, 20))
        
        # Resumen
        story.append(Paragraph("Resumen del Período", self.styles['CustomHeading']))
        
        summary_info = [
            ['Total de Equipos:', str(monthly_data['total_devices'])],
            ['Costo Total:', f"{company.currency} {monthly_data['total_cost']:.2f}"]
        ]
        
        summary_table = Table(summary_info, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detalle por equipo
        if monthly_data['devices']:
            story.append(Paragraph("Detalle por Equipo", self.styles['CustomHeading']))
            
            device_data = [['Equipo', 'Estado', 'Días', 'Costo Base', 'Costo Almac.', 'Total']]
            
            for device_cost in monthly_data['devices']:
                device_data.append([
                    device_cost['device_name'][:20] + ('...' if len(device_cost['device_name']) > 20 else ''),
                    device_cost['status'].replace('_', ' ')[:10],
                    str(device_cost['days_stored']),
                    f"{company.currency} {device_cost['base_cost']:.2f}",
                    f"{company.currency} {device_cost['storage_cost']:.2f}",
                    f"{company.currency} {device_cost['total_cost']:.2f}"
                ])
            
            device_table = Table(device_data, colWidths=[2*inch, 1*inch, 0.7*inch, 1*inch, 1*inch, 1*inch])
            device_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(device_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_device_cost_report_csv(self, device: Device, calculation_date: Optional[date] = None) -> str:
        """Genera reporte CSV de costo de un dispositivo específico"""
        cost_data = self.cost_calculator.calculate_device_cost(device, calculation_date)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados de información general
        writer.writerow(['REPORTE DE COSTO DE EQUIPO'])
        writer.writerow([])
        writer.writerow(['Empresa', device.company.name])
        writer.writerow(['RUT/ID', device.company.rut_id or 'N/A'])
        writer.writerow(['Moneda', device.company.currency])
        writer.writerow(['Fecha de generación', datetime.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Información del equipo
        writer.writerow(['INFORMACIÓN DEL EQUIPO'])
        writer.writerow(['Nombre', device.name])
        writer.writerow(['Número de Serie', device.serial_number or 'N/A'])
        writer.writerow(['Marca', device.brand or 'N/A'])
        writer.writerow(['Modelo', device.model or 'N/A'])
        writer.writerow(['Estado', device.status.replace('_', ' ').title()])
        writer.writerow(['Ubicación', device.location.name if device.location else 'Sin ubicación'])
        writer.writerow(['Fecha de Ingreso', cost_data['entry_date']])
        writer.writerow(['Fecha de Cálculo', cost_data['calculation_date']])
        writer.writerow([])
        
        # Desglose de costos
        writer.writerow(['DESGLOSE DE COSTOS'])
        writer.writerow(['Concepto', 'Cantidad', 'Precio Unitario', 'Total'])
        writer.writerow(['Costo Base', '1', f"{cost_data['base_cost']:.2f}", f"{cost_data['base_cost']:.2f}"])
        writer.writerow(['Almacenamiento', f"{cost_data['days_stored']} días", f"{cost_data['daily_cost']:.2f}", f"{cost_data['storage_cost']:.2f}"])
        writer.writerow(['', '', 'Subtotal', f"{cost_data['subtotal']:.2f}"])
        
        if cost_data['apply_iva'] and cost_data['iva_amount'] > 0:
            writer.writerow(['', '', f"IVA ({cost_data['iva_percent']:.0f}%)", f"{cost_data['iva_amount']:.2f}"])
        
        writer.writerow(['', '', 'TOTAL', f"{cost_data['total_cost']:.2f}"])
        
        return output.getvalue()
    
    def generate_company_monthly_report_csv(self, company: Company, year: int, month: int) -> str:
        """Genera reporte CSV mensual de una empresa"""
        monthly_data = self.cost_calculator.calculate_company_monthly_cost(company, year, month)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([f'REPORTE MENSUAL - {monthly_data["month_name"]} {year}'])
        writer.writerow([])
        writer.writerow(['Empresa', company.name])
        writer.writerow(['RUT/ID', company.rut_id or 'N/A'])
        writer.writerow(['Período', monthly_data['period']])
        writer.writerow(['Moneda', company.currency])
        writer.writerow(['Fecha de generación', datetime.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Resumen
        writer.writerow(['RESUMEN DEL PERÍODO'])
        writer.writerow(['Total de Equipos', monthly_data['total_devices']])
        writer.writerow(['Costo Total', f"{monthly_data['total_cost']:.2f}"])
        writer.writerow([])
        
        # Detalle por equipo
        if monthly_data['devices']:
            writer.writerow(['DETALLE POR EQUIPO'])
            writer.writerow(['Equipo', 'Estado', 'Ubicación', 'Días Almacenado', 'Costo Base', 'Costo Almacenamiento', 'Subtotal', 'IVA', 'Total'])
            
            for device_cost in monthly_data['devices']:
                writer.writerow([
                    device_cost['device_name'],
                    device_cost['status'].replace('_', ' ').title(),
                    device_cost.get('location', 'Sin ubicación'),
                    device_cost['days_stored'],
                    f"{device_cost['base_cost']:.2f}",
                    f"{device_cost['storage_cost']:.2f}",
                    f"{device_cost['subtotal']:.2f}",
                    f"{device_cost['iva_amount']:.2f}",
                    f"{device_cost['total_cost']:.2f}"
                ])
        
        return output.getvalue()
    
    def generate_devices_list_csv(self, devices: List[Device]) -> str:
        """Genera CSV con lista de dispositivos y sus costos actuales"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow(['LISTA DE EQUIPOS Y COSTOS'])
        writer.writerow([])
        writer.writerow(['Fecha de generación', datetime.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Encabezados de datos
        writer.writerow([
            'ID', 'Nombre', 'Empresa', 'Serie', 'Marca', 'Modelo', 'Estado', 
            'Ubicación', 'Fecha Ingreso', 'Días Almacenado', 'Costo Base', 
            'Costo Diario', 'Costo Almacenamiento', 'Costo Total'
        ])
        
        # Datos de dispositivos
        for device in devices:
            cost_data = self.cost_calculator.calculate_device_cost(device)
            
            writer.writerow([
                device.id,
                device.name,
                device.company.name,
                device.serial_number or '',
                device.brand or '',
                device.model or '',
                device.status.replace('_', ' ').title(),
                device.location.name if device.location else '',
                cost_data['entry_date'],
                cost_data['days_stored'],
                f"{cost_data['base_cost']:.2f}",
                f"{cost_data['daily_cost']:.2f}",
                f"{cost_data['storage_cost']:.2f}",
                f"{cost_data['total_cost']:.2f}"
            ])
        
        return output.getvalue()