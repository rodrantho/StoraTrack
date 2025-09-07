from datetime import datetime, timezone
import time
from app.config import settings

def get_local_timezone():
    """Obtiene la zona horaria local del sistema"""
    return timezone.utc if time.daylight == 0 else timezone.utc

def now_local():
    """Obtiene la fecha y hora actual en la zona horaria local"""
    return datetime.now()

def utc_to_local(utc_dt):
    """Convierte una fecha UTC a la zona horaria local"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        # Asumir que es UTC si no tiene timezone info
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone()

def local_to_utc(local_dt):
    """Convierte una fecha local a UTC"""
    if local_dt is None:
        return None
    if local_dt.tzinfo is None:
        # Asumir que es local si no tiene timezone info
        local_dt = local_dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return local_dt.astimezone(timezone.utc)

def format_datetime(dt, format_str=None):
    """Formatea una fecha usando el formato configurado"""
    if dt is None:
        return None
    if format_str is None:
        format_str = settings.datetime_format
    # Convertir a local si es necesario
    if dt.tzinfo is not None:
        dt = utc_to_local(dt)
    return dt.strftime(format_str)

def format_date(dt, format_str=None):
    """Formatea una fecha usando el formato configurado"""
    if dt is None:
        return None
    if format_str is None:
        format_str = settings.date_format
    # Convertir a local si es necesario
    if dt.tzinfo is not None:
        dt = utc_to_local(dt)
    return dt.strftime(format_str)