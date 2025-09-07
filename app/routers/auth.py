from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserLogin, Token, User as UserSchema, UserProfileUpdate
from app.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_current_active_user,
    get_password_hash,
    verify_password
)
from app.config import settings
from app.utils.datetime_utils import now_local

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse, name="auth_login")
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login", name="auth_login_post")
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
    user.last_login = now_local()
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
    user.last_login = now_local()
    db.commit()
    
    # Crear token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/logout", name="auth_logout")
async def logout(request: Request):
    """Logout"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@router.post("/logout", name="auth_logout_post")
async def logout_post(request: Request):
    """Logout POST"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@router.get("/me", response_model=UserSchema, name="auth_me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/check", name="auth_check")
async def check_auth(request: Request, db: Session = Depends(get_db)):
    """Verificar estado de autenticación"""
    try:
        user_id = request.session.get("user_id")
        if user_id:
            # Verificar que el usuario aún existe y está activo
            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if user:
                return {
                    "authenticated": True,
                    "user_id": user_id,
                    "user_email": request.session.get("user_email"),
                    "user_role": request.session.get("user_role"),
                    "company_id": request.session.get("company_id"),
                    "session_data": dict(request.session)
                }
            else:
                # Usuario no existe o está inactivo, limpiar sesión
                request.session.clear()
                return {"authenticated": False, "reason": "user_not_found_or_inactive"}
        return {"authenticated": False, "reason": "no_session"}
    except Exception as e:
        return {"authenticated": False, "reason": f"error: {str(e)}"}

@router.get("/profile", response_class=HTMLResponse, name="auth_profile")
async def profile_page(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Página de perfil de usuario"""
    return templates.TemplateResponse("auth/profile.html", {
        "request": request,
        "current_user": current_user
    })

@router.post("/profile", name="auth_profile_update")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    current_password: str = Form(None),
    new_password: str = Form(None),
    confirm_password: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar perfil de usuario"""
    errors = []
    
    # Validar email único
    if email != current_user.email:
        existing_user = db.query(User).filter(User.email == email, User.id != current_user.id).first()
        if existing_user:
            errors.append("El email ya está en uso por otro usuario")
    
    # Validar cambio de contraseña
    if new_password:
        if not current_password:
            errors.append("Debe proporcionar la contraseña actual para cambiarla")
        elif not verify_password(current_password, current_user.hashed_password):
            errors.append("La contraseña actual es incorrecta")
        elif len(new_password) < 6:
            errors.append("La nueva contraseña debe tener al menos 6 caracteres")
        elif new_password != confirm_password:
            errors.append("Las contraseñas no coinciden")
    
    if errors:
        return templates.TemplateResponse("auth/profile.html", {
            "request": request,
            "current_user": current_user,
            "errors": errors,
            "full_name": full_name,
            "email": email
        }, status_code=400)
    
    # Actualizar datos
    current_user.full_name = full_name
    current_user.email = email
    
    if new_password:
        current_user.hashed_password = get_password_hash(new_password)
    
    current_user.updated_at = now_local()
    db.commit()
    
    # Actualizar sesión si cambió el email
    if email != request.session.get("user_email"):
        request.session["user_email"] = email
    
    return templates.TemplateResponse("auth/profile.html", {
        "request": request,
        "current_user": current_user,
        "success": "Perfil actualizado correctamente"
    })