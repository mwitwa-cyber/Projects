from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from jose import JWTError, jwt
import pyotp
import qrcode
import io
import base64

from app.services.auth_service import (
    authenticate_user, create_access_token, get_password_hash, 
    validate_password_strength, SECRET_KEY, ALGORITHM
)
from app.models.user import User
from app.models.base import get_db

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validate JWT token and return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Check token expiration is handled by jwt.decode automatically
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Return current active user."""
    return current_user


class UserCreate(BaseModel):
    """User registration request model with validation."""
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v


class UserLogin(BaseModel):
    """User login request model."""
    username: str
    password: str
    totp_code: Optional[str] = None


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with password strength validation."""
    # Check for existing user (case-insensitive)
    existing_user = db.query(User).filter(
        (User.username == user.username.lower()) | (User.email == user.email.lower())
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username.lower(), 
        email=user.email.lower(), 
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    db_user = authenticate_user(db, user.username, user.password)
    
    if not db_user:
        # Use constant-time response to prevent timing attacks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )
    
    # Check if TOTP is enabled
    if db_user.totp_enabled:
        if not user.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="TOTP code required",
                headers={"X-TOTP-Required": "true"}
            )
        
        if not db_user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="TOTP configuration error"
            )
            
        totp = pyotp.TOTP(db_user.totp_secret)
        # valid_window=1 allows for minor time drift (30 seconds before/after)
        if not totp.verify(user.totp_code, valid_window=1):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid TOTP code"
            )

    access_token = create_access_token({"sub": db_user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "totp_enabled": db_user.totp_enabled,
        "username": db_user.username
    }


@router.post("/totp/setup")
def totp_setup(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP already enabled")
    
    secret = pyotp.random_base32()
    
    # Save secret temporarily? Or return it and save only on verify?
    # Better to save it but keep enabled=False until verified.
    current_user.totp_secret = secret
    db.commit()
    
    # Generate QR Code
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="LuSE Platform")
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return {"secret": secret, "qr_code": f"data:image/png;base64,{img_str}"}

class TOTPVerify(BaseModel):
    code: str

@router.post("/totp/verify")
def totp_verify(payload: TOTPVerify, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not setup")
        
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(payload.code):
        raise HTTPException(status_code=400, detail="Invalid code")
        
    current_user.totp_enabled = True
    db.commit()
    return {"status": "enabled"}

@router.post("/totp/disable")
def totp_disable(payload: TOTPVerify, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Require code to disable too
    if not current_user.totp_enabled:
         raise HTTPException(status_code=400, detail="TOTP not enabled")

    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(payload.code):
        raise HTTPException(status_code=400, detail="Invalid code")
        
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    return {"status": "disabled"}
