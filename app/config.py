import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    # App settings
    app_name: str = os.getenv("APP_NAME", "StoraTrack")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./storatrack.db")
    
    # Timezone and locale
    timezone: str = os.getenv("TIMEZONE", "America/Montevideo")
    date_format: str = "%d/%m/%Y"
    datetime_format: str = "%d/%m/%Y %H:%M"
    
    # Currency and tax
    currency: str = os.getenv("CURRENCY", "UYU")
    currency_symbol: str = os.getenv("CURRENCY_SYMBOL", "$")
    iva_percent: float = float(os.getenv("IVA_PERCENT", "22.0"))
    incluir_iva: bool = os.getenv("INCLUIR_IVA", "true").lower() == "true"
    
    # Company branding
    company_logo_url: str = os.getenv("COMPANY_LOGO_URL", "/static/images/logo.png")
    company_name: str = os.getenv("COMPANY_NAME", "StoraTrack")
    
    # File uploads
    upload_dir: str = "uploads"
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_extensions: list = [".jpg", ".jpeg", ".png", ".pdf"]
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Email settings (for future use)
    smtp_server: Optional[str] = os.getenv("SMTP_SERVER")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()