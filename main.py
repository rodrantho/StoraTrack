from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from app.database import engine, get_db
from app.models import Base
from app.routers import auth, admin, client, api
from app.api import cost_reports, labels
from app.config import settings
from app.auth import get_current_user

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="StoraTrack",
    description="Sistema de gestión de almacenamiento multi-tenant",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Custom middleware for handling authentication redirects
class AuthRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Si es una respuesta 401 y es una petición web (no API), redirigir al login
        if response.status_code == 401:
            # Verificar si es una petición de API o web
            if request.url.path.startswith('/api/') or request.headers.get('accept', '').startswith('application/json'):
                # Para API, devolver JSON
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Acceso denegado"}
                )
            else:
                # Para web, redirigir al login
                return RedirectResponse(url="/auth/login", status_code=302)
        
        return response

# Add middleware
# Add custom auth redirect middleware first
app.add_middleware(AuthRedirectMiddleware)

# CORS configuration - allow local network access
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:4011,http://127.0.0.1:4011").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Trusted hosts - allow local network access
allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*").split(",")
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=60 * 60 * 24 * 7,  # 7 días
    same_site='lax',  # Permite que la cookie se envíe en navegaciones normales
    https_only=False,  # Permitir HTTP en desarrollo local
    session_cookie='storatrack_session'  # Nombre específico para la cookie
)

# Mount static files
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(client.router, prefix="/client", tags=["client"])
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(cost_reports.router, tags=["cost-reports"])
app.include_router(labels.router, tags=["labels"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Página principal - redirige según el usuario"""
    # Obtener usuario actual si existe
    current_user = None
    try:
        from app.auth import get_current_user
        current_user = get_current_user(request, db)
    except HTTPException:
        # Usuario no autenticado, continuar sin usuario
        current_user = None
    except Exception:
        # Cualquier otro error, continuar sin usuario
        current_user = None
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/app-info", response_class=HTMLResponse)
async def app_info(request: Request, db: Session = Depends(get_db)):
    """Página de información técnica de la aplicación"""
    # Obtener usuario actual si existe
    current_user = None
    try:
        from app.auth import get_current_user
        current_user = get_current_user(request, db)
    except HTTPException:
        # Usuario no autenticado, continuar sin usuario
        current_user = None
    except Exception:
        # Cualquier otro error, continuar sin usuario
        current_user = None
    
    return templates.TemplateResponse("app_info.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": "StoraTrack"}

@app.get("/@vite/client")
async def vite_client_handler():
    """Maneja requests de desarrollo de Vite para evitar 404 en producción"""
    return {"message": "Vite client not available in production"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4011,
        reload=False,  # Desactivar reload para producción
        access_log=True,
        log_level="info"
    )