from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.schemas import TokenData
from app.config import settings
from app.utils.datetime_utils import now_local

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashear contraseña"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = now_local() + expires_delta
    else:
        expire = now_local() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """Verificar token JWT"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
        return token_data
    except JWTError:
        raise credentials_exception

def authenticate_user(db: Session, email: str, password: str):
    """Autenticar usuario"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    if not user.is_active:
        return False
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Obtener usuario actual desde sesión o token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acceso denegado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Primero intentar obtener desde sesión (para web)
    user_id = request.session.get("user_id")
    if user_id:
        try:
            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if user:
                # Verificar que la sesión tenga todos los datos necesarios
                if not request.session.get("user_email") or not request.session.get("user_role"):
                    # Regenerar datos de sesión
                    request.session["user_email"] = user.email
                    request.session["user_role"] = user.role.value
                    request.session["company_id"] = user.company_id
                return user
            else:
                # Usuario no encontrado o inactivo, limpiar sesión
                request.session.clear()
        except Exception as e:
            # Solo limpiar sesión si hay error de base de datos
            print(f"Error al verificar usuario en sesión: {e}")
            request.session.clear()
    
    # Si no hay sesión, intentar con token JWT (para API)
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            token_data = verify_token(token, credentials_exception)
            user = db.query(User).filter(User.email == token_data.email, User.is_active == True).first()
            if user is None:
                raise credentials_exception
            return user
        except Exception as e:
            # Error con token JWT, no limpiar sesión
            print(f"Error al verificar token JWT: {e}")
    
    raise credentials_exception

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Obtener usuario activo actual"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def require_role(allowed_roles: list):
    """Decorator para requerir roles específicos"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este recurso"
            )
        return current_user
    return role_checker

def require_superadmin(current_user: User = Depends(get_current_active_user)):
    """Requerir rol de superadmin"""
    if current_user.role.value != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de superadministrador"
        )
    return current_user

def require_admin_or_staff(current_user: User = Depends(get_current_active_user)):
    """Requerir rol de admin o staff"""
    if current_user.role.value not in ["superadmin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador o staff"
        )
    return current_user

def require_same_company_or_admin(current_user: User = Depends(get_current_active_user)):
    """Requerir misma empresa o permisos de admin"""
    def company_checker(company_id: int):
        if current_user.role.value in ["superadmin", "staff"]:
            return current_user
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a los datos de esta empresa"
            )
        return current_user
    return company_checker

def get_user_permissions(user: User) -> dict:
    """Obtener permisos del usuario"""
    permissions = {
        "can_manage_companies": False,
        "can_manage_users": False,
        "can_manage_all_devices": False,
        "can_manage_own_devices": False,
        "can_view_reports": False,
        "can_generate_reports": False,
        "can_close_months": False,
        "can_view_audit_logs": False,
    }
    
    if user.role.value == "superadmin":
        # Superadmin puede hacer todo
        for key in permissions:
            permissions[key] = True
    elif user.role.value == "staff":
        # Staff puede gestionar empresas, usuarios, dispositivos y generar reportes
        permissions.update({
            "can_manage_companies": True,
            "can_manage_users": True,
            "can_manage_all_devices": True,
            "can_view_reports": True,
            "can_generate_reports": True,
            "can_close_months": True,
            "can_view_audit_logs": True,
        })
    elif user.role.value == "client_user":
        # Cliente solo puede ver sus propios dispositivos y reportes
        permissions.update({
            "can_manage_own_devices": True,
            "can_view_reports": True,
        })
    
    return permissions

def check_company_access(user: User, company_id: int) -> bool:
    """Verificar si el usuario tiene acceso a una empresa específica"""
    if user.role.value in ["superadmin", "staff"]:
        return True
    return user.company_id == company_id

def get_accessible_companies(user: User, db: Session) -> list:
    """Obtener empresas accesibles para el usuario"""
    from app.models import Company
    
    if user.role.value in ["superadmin", "staff"]:
        return db.query(Company).filter(Company.is_active == True).all()
    elif user.role.value == "client_user" and user.company_id:
        return db.query(Company).filter(
            Company.id == user.company_id,
            Company.is_active == True
        ).all()
    return []