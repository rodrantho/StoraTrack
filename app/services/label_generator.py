from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
from barcode import Code128
import base64
from typing import Optional, Tuple
from datetime import datetime

class LabelGenerator:
    """Servicio para generar etiquetas QR y códigos de barras"""
    
    def __init__(self):
        self.qr_size = (200, 200)
        self.barcode_size = (300, 100)
        self.label_size = (400, 600)  # Tamaño de etiqueta completa
    
    def generate_qr_code(self, data: str, size: Optional[Tuple[int, int]] = None) -> str:
        """Genera un código QR y retorna la imagen en base64"""
        if size is None:
            size = self.qr_size
            
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Crear imagen QR
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
        
        # Convertir a base64
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_barcode(self, data: str, size: Optional[Tuple[int, int]] = None) -> str:
        """Genera un código de barras Code128 y retorna la imagen en base64"""
        if size is None:
            size = self.barcode_size
            
        # Crear código de barras
        code128 = Code128(data, writer=ImageWriter())
        
        # Generar imagen
        buffer = BytesIO()
        code128.write(buffer, options={
            'module_width': 0.2,
            'module_height': 15.0,
            'quiet_zone': 6.5,
            'font_size': 10,
            'text_distance': 5.0,
            'background': 'white',
            'foreground': 'black',
        })
        
        # Redimensionar si es necesario
        img = Image.open(buffer)
        if img.size != size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_device_label(self, device_data: dict) -> str:
        """Genera una etiqueta completa para un dispositivo con QR, código de barras e información"""
        # Crear imagen base
        img = Image.new('RGB', self.label_size, 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Intentar cargar fuente
            title_font = ImageFont.truetype("arial.ttf", 16)
            text_font = ImageFont.truetype("arial.ttf", 12)
            small_font = ImageFont.truetype("arial.ttf", 10)
        except:
            # Usar fuente por defecto si no se encuentra arial
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        y_offset = 20
        
        # Título
        company_name = device_data.get('company_name', 'StoraTrack')
        draw.text((20, y_offset), company_name, fill='black', font=title_font)
        y_offset += 30
        
        # Información del dispositivo
        device_name = device_data.get('name', 'Dispositivo')
        draw.text((20, y_offset), f"Equipo: {device_name}", fill='black', font=text_font)
        y_offset += 20
        
        serial_number = device_data.get('serial_number', '')
        if serial_number:
            draw.text((20, y_offset), f"S/N: {serial_number}", fill='black', font=text_font)
            y_offset += 20
        
        location = device_data.get('location', '')
        if location:
            draw.text((20, y_offset), f"Ubicación: {location}", fill='black', font=text_font)
            y_offset += 20
        
        entry_date = device_data.get('entry_date', '')
        if entry_date:
            if isinstance(entry_date, datetime):
                entry_date = entry_date.strftime('%d/%m/%Y')
            draw.text((20, y_offset), f"Ingreso: {entry_date}", fill='black', font=small_font)
            y_offset += 20
        
        y_offset += 10
        
        # Generar QR code
        device_id = device_data.get('id', '')
        qr_data = f"DEVICE:{device_id}:{serial_number}"
        qr_img_data = self.generate_qr_code(qr_data, (150, 150))
        
        # Decodificar QR y pegarlo en la etiqueta
        qr_img_bytes = base64.b64decode(qr_img_data.split(',')[1])
        qr_img = Image.open(BytesIO(qr_img_bytes))
        img.paste(qr_img, (20, y_offset))
        
        # Texto QR
        draw.text((180, y_offset + 60), "Código QR", fill='black', font=small_font)
        draw.text((180, y_offset + 75), f"ID: {device_id}", fill='black', font=small_font)
        
        y_offset += 170
        
        # Generar código de barras
        barcode_data = f"{device_id:06d}"  # Formatear ID como 6 dígitos
        barcode_img_data = self.generate_barcode(barcode_data, (350, 80))
        
        # Decodificar código de barras y pegarlo en la etiqueta
        barcode_img_bytes = base64.b64decode(barcode_img_data.split(',')[1])
        barcode_img = Image.open(BytesIO(barcode_img_bytes))
        img.paste(barcode_img, (25, y_offset))
        
        y_offset += 90
        
        # Información adicional
        draw.text((20, y_offset), f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                 fill='gray', font=small_font)
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_location_label(self, location_data: dict) -> str:
        """Genera una etiqueta para una ubicación"""
        # Crear imagen base
        img = Image.new('RGB', (300, 400), 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 16)
            text_font = ImageFont.truetype("arial.ttf", 12)
            small_font = ImageFont.truetype("arial.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        y_offset = 20
        
        # Título
        company_name = location_data.get('company_name', 'StoraTrack')
        draw.text((20, y_offset), company_name, fill='black', font=title_font)
        y_offset += 30
        
        # Información de la ubicación
        location_name = location_data.get('name', 'Ubicación')
        draw.text((20, y_offset), f"Ubicación: {location_name}", fill='black', font=text_font)
        y_offset += 20
        
        location_code = location_data.get('code', '')
        if location_code:
            draw.text((20, y_offset), f"Código: {location_code}", fill='black', font=text_font)
            y_offset += 20
        
        max_capacity = location_data.get('max_capacity')
        if max_capacity:
            draw.text((20, y_offset), f"Capacidad: {max_capacity}", fill='black', font=text_font)
            y_offset += 20
        
        y_offset += 10
        
        # Generar QR code para ubicación
        location_id = location_data.get('id', '')
        qr_data = f"LOCATION:{location_id}:{location_code}"
        qr_img_data = self.generate_qr_code(qr_data, (120, 120))
        
        # Decodificar QR y pegarlo en la etiqueta
        qr_img_bytes = base64.b64decode(qr_img_data.split(',')[1])
        qr_img = Image.open(BytesIO(qr_img_bytes))
        img.paste(qr_img, (90, y_offset))
        
        y_offset += 140
        
        # Información adicional
        draw.text((20, y_offset), f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                 fill='gray', font=small_font)
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def get_device_qr_url(self, device_id: int, base_url: str = "") -> str:
        """Genera URL para acceso directo al dispositivo via QR"""
        return f"{base_url}/device/{device_id}"
    
    def get_location_qr_url(self, location_id: int, base_url: str = "") -> str:
        """Genera URL para acceso directo a la ubicación via QR"""
        return f"{base_url}/location/{location_id}"