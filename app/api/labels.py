from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
import base64
from io import BytesIO

from app.database import get_db
from app.models import Device, Location, Company
from app.auth import get_current_user
from app.services.label_generator import LabelGenerator
from app.schemas import User

router = APIRouter(prefix="/api/labels")
label_generator = LabelGenerator()

@router.get("/device/{device_id}/qr")
async def get_device_qr(
    device_id: int,
    size: Optional[int] = Query(200, description="Tamaño del QR en píxeles"),
    format: Optional[str] = Query("base64", description="Formato de salida: base64 o png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera código QR para un dispositivo"""
    
    # Verificar que el dispositivo existe y el usuario tiene acceso
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Verificar acceso según rol
    if current_user.role == "client" and device.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este dispositivo")
    
    # Generar datos del QR
    qr_data = f"DEVICE:{device.id}:{device.serial_number or ''}"
    
    # Generar QR
    qr_image = label_generator.generate_qr_code(qr_data, (size, size))
    
    if format == "base64":
        return {"qr_code": qr_image, "data": qr_data}
    elif format == "png":
        # Decodificar base64 y retornar como imagen
        img_data = base64.b64decode(qr_image.split(',')[1])
        return Response(content=img_data, media_type="image/png")
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado")

@router.get("/device/{device_id}/barcode")
async def get_device_barcode(
    device_id: int,
    width: Optional[int] = Query(300, description="Ancho del código de barras"),
    height: Optional[int] = Query(100, description="Alto del código de barras"),
    format: Optional[str] = Query("base64", description="Formato de salida: base64 o png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera código de barras Code128 para un dispositivo"""
    
    # Verificar que el dispositivo existe y el usuario tiene acceso
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Verificar acceso según rol
    if current_user.role == "client" and device.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este dispositivo")
    
    # Generar código de barras con ID del dispositivo
    barcode_data = f"{device.id:06d}"  # Formatear como 6 dígitos
    
    # Generar código de barras
    barcode_image = label_generator.generate_barcode(barcode_data, (width, height))
    
    if format == "base64":
        return {"barcode": barcode_image, "data": barcode_data}
    elif format == "png":
        # Decodificar base64 y retornar como imagen
        img_data = base64.b64decode(barcode_image.split(',')[1])
        return Response(content=img_data, media_type="image/png")
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado")

@router.get("/device/{device_id}/label")
async def get_device_label(
    device_id: int,
    format: Optional[str] = Query("base64", description="Formato de salida: base64 o png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera etiqueta completa para un dispositivo"""
    
    # Verificar que el dispositivo existe y el usuario tiene acceso
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Verificar acceso según rol
    if current_user.role == "client" and device.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este dispositivo")
    
    # Obtener información de la empresa
    company = db.query(Company).filter(Company.id == device.company_id).first()
    
    # Obtener información de la ubicación
    location = None
    if device.location_id:
        location = db.query(Location).filter(Location.id == device.location_id).first()
    
    # Preparar datos para la etiqueta
    device_data = {
        "id": device.id,
        "name": device.name,
        "serial_number": device.serial_number,
        "company_name": company.name if company else "StoraTrack",
        "location": location.name if location else "",
        "entry_date": device.entry_date
    }
    
    # Generar etiqueta
    label_image = label_generator.generate_device_label(device_data)
    
    if format == "base64":
        return {"label": label_image, "device_data": device_data}
    elif format == "png":
        # Decodificar base64 y retornar como imagen
        img_data = base64.b64decode(label_image.split(',')[1])
        return Response(content=img_data, media_type="image/png")
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado")

@router.get("/location/{location_id}/qr")
async def get_location_qr(
    location_id: int,
    size: Optional[int] = Query(200, description="Tamaño del QR en píxeles"),
    format: Optional[str] = Query("base64", description="Formato de salida: base64 o png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera código QR para una ubicación"""
    
    # Verificar que la ubicación existe y el usuario tiene acceso
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    # Verificar acceso según rol
    if current_user.role == "client" and location.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta ubicación")
    
    # Generar datos del QR
    qr_data = f"LOCATION:{location.id}:{location.code or ''}"
    
    # Generar QR
    qr_image = label_generator.generate_qr_code(qr_data, (size, size))
    
    if format == "base64":
        return {"qr_code": qr_image, "data": qr_data}
    elif format == "png":
        # Decodificar base64 y retornar como imagen
        img_data = base64.b64decode(qr_image.split(',')[1])
        return Response(content=img_data, media_type="image/png")
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado")

@router.get("/location/{location_id}/label")
async def get_location_label(
    location_id: int,
    format: Optional[str] = Query("base64", description="Formato de salida: base64 o png"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera etiqueta completa para una ubicación"""
    
    # Verificar que la ubicación existe y el usuario tiene acceso
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    # Verificar acceso según rol
    if current_user.role == "client" and location.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta ubicación")
    
    # Obtener información de la empresa
    company = db.query(Company).filter(Company.id == location.company_id).first()
    
    # Preparar datos para la etiqueta
    location_data = {
        "id": location.id,
        "name": location.name,
        "code": location.code,
        "company_name": company.name if company else "StoraTrack",
        "max_capacity": location.max_capacity
    }
    
    # Generar etiqueta
    label_image = label_generator.generate_location_label(location_data)
    
    if format == "base64":
        return {"label": label_image, "location_data": location_data}
    elif format == "png":
        # Decodificar base64 y retornar como imagen
        img_data = base64.b64decode(label_image.split(',')[1])
        return Response(content=img_data, media_type="image/png")
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado")

@router.get("/batch/devices")
async def get_batch_device_labels(
    device_ids: str = Query(..., description="IDs de dispositivos separados por comas"),
    label_type: str = Query("label", description="Tipo: qr, barcode, o label"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Genera etiquetas en lote para múltiples dispositivos"""
    
    try:
        # Parsear IDs
        ids = [int(id.strip()) for id in device_ids.split(',') if id.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="IDs de dispositivos inválidos")
    
    if len(ids) > 50:  # Limitar a 50 dispositivos por lote
        raise HTTPException(status_code=400, detail="Máximo 50 dispositivos por lote")
    
    # Obtener dispositivos
    devices = db.query(Device).filter(Device.id.in_(ids)).all()
    
    # Verificar acceso
    if current_user.role == "client":
        for device in devices:
            if device.company_id != current_user.company_id:
                raise HTTPException(status_code=403, detail=f"No tienes acceso al dispositivo {device.id}")
    
    results = []
    
    for device in devices:
        try:
            if label_type == "qr":
                qr_data = f"DEVICE:{device.id}:{device.serial_number or ''}"
                image = label_generator.generate_qr_code(qr_data)
                results.append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "image": image,
                    "type": "qr"
                })
            elif label_type == "barcode":
                barcode_data = f"{device.id:06d}"
                image = label_generator.generate_barcode(barcode_data)
                results.append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "image": image,
                    "type": "barcode"
                })
            elif label_type == "label":
                # Obtener datos adicionales
                company = db.query(Company).filter(Company.id == device.company_id).first()
                location = None
                if device.location_id:
                    location = db.query(Location).filter(Location.id == device.location_id).first()
                
                device_data = {
                    "id": device.id,
                    "name": device.name,
                    "serial_number": device.serial_number,
                    "company_name": company.name if company else "StoraTrack",
                    "location": location.name if location else "",
                    "entry_date": device.entry_date
                }
                
                image = label_generator.generate_device_label(device_data)
                results.append({
                    "device_id": device.id,
                    "device_name": device.name,
                    "image": image,
                    "type": "label"
                })
            else:
                raise HTTPException(status_code=400, detail="Tipo de etiqueta no soportado")
                
        except Exception as e:
            results.append({
                "device_id": device.id,
                "device_name": device.name,
                "error": str(e),
                "type": label_type
            })
    
    return {
        "results": results,
        "total_requested": len(ids),
        "total_generated": len([r for r in results if "image" in r]),
        "total_errors": len([r for r in results if "error" in r])
    }