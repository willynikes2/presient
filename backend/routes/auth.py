"""
Authentication routes with comprehensive validation
Replace your current backend/routes/auth.py with this complete file
"""

from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import re
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# ==================== Configuration ====================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# ==================== Pydantic Models ====================

class UserRegister(BaseModel):
    """User registration model with validation"""
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    
    @field_validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None

class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v

# ==================== Mock Database ====================
# TODO: Replace this with your actual database integration
users_db = {
    "testuser": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": pwd_context.hash("TestPass123!"),
        "full_name": "Test User",
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
}

# ==================== Helper Functions ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username - TODO: Replace with database query"""
    return users_db.get(username)

async def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email - TODO: Replace with database query"""
    for user in users_db.values():
        if user["email"] == email:
            return user
    return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "INVALID_CREDENTIALS",
            "message": "Could not validate credentials"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "access":
            raise credentials_exception
            
        token_data = TokenData(username=username)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "TOKEN_INVALID",
                "message": "Token validation failed",
                "details": str(e)
            }
        )
    
    user = await get_user_by_username(username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "USER_NOT_FOUND",
                "message": "User no longer exists"
            }
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "USER_INACTIVE",
                "message": "User account is disabled"
            }
        )
    
    return user

# ==================== Routes ====================

# Keep your existing verify endpoint for backwards compatibility
@router.get("/verify")
async def verify_user(authorization: str = Header(...)):
    """Legacy verify endpoint - validates JWT token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    
    try:
        # Validate the token
        user = await get_current_user(token)
        return {
            "token": token,
            "status": "valid",
            "user_id": user["id"],
            "username": user["username"]
        }
    except HTTPException as e:
        return {
            "token": token,
            "status": "invalid",
            "error": e.detail
        }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    """Register a new user"""
    # Check if username already exists
    if await get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "USERNAME_EXISTS",
                "field": "username",
                "message": f"Username '{user.username}' is already taken"
            }
        )
    
    # Check if email already exists
    if await get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "EMAIL_EXISTS",
                "field": "email",
                "message": f"Email '{user.email}' is already registered"
            }
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    user_dict = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "full_name": user.full_name,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    }
    
    # TODO: Save to actual database instead of mock
    users_db[user.username] = user_dict
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "status": "success",
        "message": "User registered successfully",
        "user_id": user_id,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    # Get user
    user = await get_user_by_username(form_data.username)
    
    # Guard: User not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": "Incorrect username or password"
            }
        )
    
    # Guard: Invalid password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_CREDENTIALS",
                "message": "Incorrect username or password"
            }
        )
    
    # Guard: User inactive
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "USER_INACTIVE",
                "message": "Your account has been disabled"
            }
        )
    
    # Update last login
    # TODO: Update in actual database
    users_db[form_data.username]["last_login"] = datetime.now(timezone.utc)
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_REFRESH_TOKEN",
                    "message": "Invalid refresh token"
                }
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_REFRESH_TOKEN",
                "message": "Refresh token validation failed"
            }
        )
    
    # Check if user still exists and is active
    user = await get_user_by_username(username)
    if not user or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "USER_UNAVAILABLE",
                "message": "User account is no longer available"
            }
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    # Remove sensitive information
    user_info = {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "created_at": current_user["created_at"].isoformat(),
        "last_login": current_user.get("last_login").isoformat() if current_user.get("last_login") else None
    }
    
    return user_info

@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """Logout current user"""
    # In a real application, you might want to:
    # - Add the token to a blacklist
    # - Clear any server-side sessions
    # - Log the logout event
    
    return {
        "status": "success",
        "message": "Logged out successfully"
    }

@router.post("/password-reset")
async def request_password_reset(reset_request: PasswordReset):
    """Request password reset email"""
    user = await get_user_by_email(reset_request.email)
    
    # Always return success to prevent email enumeration
    # In production, send email only if user exists
    if user:
        # TODO: Generate reset token and send email
        reset_token = create_access_token(
            data={"sub": user["username"], "purpose": "reset"},
            expires_delta=timedelta(hours=1)
        )
        # TODO: Send email with reset_token
        print(f"Password reset token for {user['email']}: {reset_token}")
    
    return {
        "status": "success",
        "message": "If the email exists, a password reset link has been sent"
    }

@router.post("/password-reset/confirm")
async def confirm_password_reset(reset_confirm: PasswordResetConfirm):
    """Confirm password reset with token"""
    try:
        payload = jwt.decode(reset_confirm.token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        purpose = payload.get("purpose")
        
        if not username or purpose != "reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_RESET_TOKEN",
                    "message": "Invalid or expired reset token"
                }
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_RESET_TOKEN",
                "message": "Invalid or expired reset token"
            }
        )
    
    # Update password
    user = await get_user_by_username(username)
    if user:
        # TODO: Update in actual database
        users_db[username]["hashed_password"] = get_password_hash(reset_confirm.new_password)
        
        return {
            "status": "success",
            "message": "Password reset successfully"
        }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "USER_NOT_FOUND",
            "message": "User not found"
        }
    )

# ==================== TODO: Database Integration ====================
"""
To integrate with your actual database:

1. Replace the mock users_db with your database models
2. Update these functions to use your database:
   - get_user_by_username()
   - get_user_by_email()
   - register() - save user to database
   - login() - update last_login in database
   
Example with SQLAlchemy:

from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import User

async def get_user_by_username(username: str, db: Session = Depends(get_db)) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()
"""