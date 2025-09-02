from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserLogin, Token, User as UserSchema
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_current_active_user
)
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Procesar login"""
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html", 
            {
                "request": request, 
                "error": "Email o contraseña incorrectos"
            },
            status_code=400
        )
    
    # Actualizar último login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Crear sesión
    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_role"] = user.role.value
    request.session["company_id"] = user.company_id
    
    # Redirigir según el rol
    if user.role.value in ["superadmin", "staff"]:
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/client/dashboard", status_code=302)

@router.post("/api/login", response_model=Token)
async def api_login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login para API (retorna JWT)"""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/logout")
async def logout(request: Request):
    """Logout"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@router.post("/logout")
async def logout_post(request: Request):
    """Logout POST"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/check")
async def check_auth(request: Request):
    """Verificar estado de autenticación"""
    try:
        user_id = request.session.get("user_id")
        if user_id:
            return {
                "authenticated": True,
                "user_id": user_id,
                "user_email": request.session.get("user_email"),
                "user_role": request.session.get("user_role"),
                "company_id": request.session.get("company_id")
            }
        return {"authenticated": False}
    except Exception:
        return {"authenticated": False}