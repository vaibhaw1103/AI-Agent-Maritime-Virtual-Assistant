#!/usr/bin/env python3
"""
🔐 MARITIME ASSISTANT - AUTHENTICATION & SECURITY MODULE
========================================================

Comprehensive JWT-based authentication system with:
- User registration and login
- JWT token generation and validation
- Password hashing with bcrypt
- Protected route decorators
- Role-based access control
- Session management
- Security utilities

Version: 1.0
Date: August 22, 2025
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import secrets
import logging
import json
import os
from pathlib import Path
from config import config

# Setup logging
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = config.SECRET_KEY if hasattr(config, 'SECRET_KEY') else secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token handler
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    company: Optional[str] = Field(None, max_length=100, description="Company/Organization")
    role: str = Field("user", description="User role (user, admin, viewer)")

class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None

class User(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    role: str = "user"
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

# Persistent storage using JSON file (temporary solution until PostgreSQL integration)
import json
import os
from pathlib import Path

USERS_FILE = Path("users_data.json")

def load_users_db():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                data = json.load(f)
                # Convert back to User objects
                users_db = {}
                for key, value in data.items():
                    if key.endswith('_password'):
                        users_db[key] = value  # Keep password hashes as strings
                    elif isinstance(value, dict) and 'user_id' in value:
                        # Convert dict back to User object
                        user = User(**value)
                        users_db[key] = user
                    else:
                        users_db[key] = value
                return users_db
        except Exception as e:
            logger.error(f"Failed to load users from file: {e}")
            return {}
    return {}

def save_users_db(users_db):
    """Save users to JSON file"""
    try:
        # Convert User objects to dicts for JSON serialization
        serializable_data = {}
        for key, value in users_db.items():
            if isinstance(value, User):
                serializable_data[key] = value.model_dump()
            else:
                serializable_data[key] = value
        
        with open(USERS_FILE, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save users to file: {e}")

# Load existing users or create empty dict
users_db = load_users_db()
active_tokens = set()

class AuthenticationService:
    """Comprehensive authentication service"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*(),.?\":{}|<>" for c in password)
        
        if not (has_upper and has_lower):
            return False, "Password must contain both uppercase and lowercase letters"
        
        if not has_digit:
            return False, "Password must contain at least one number"
        
        if not has_special:
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        # Track active token
        active_tokens.add(encoded_jwt)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        active_tokens.add(encoded_jwt)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            # Check if token is active
            if token not in active_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            exp_timestamp: int = payload.get("exp")
            
            if username is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Check expiration
            exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
            if datetime.utcnow() > exp_datetime:
                active_tokens.discard(token)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return TokenData(
                username=username,
                user_id=user_id,
                role=role,
                exp=exp_datetime
            )
            
        except jwt.ExpiredSignatureError:
            active_tokens.discard(token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def get_user(user_id: str) -> Optional[User]:
        """Get user by ID"""
        return users_db.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        for key, value in users_db.items():
            # Skip password entries
            if key.endswith('_password'):
                continue
            # Only check User objects
            if isinstance(value, User) and (value.username == username or value.email == username):
                return value
        return None
    
    @staticmethod
    def create_user(user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if username or email already exists
        if AuthenticationService.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        for key, value in users_db.items():
            # Skip password entries and only check User objects
            if key.endswith('_password') or not isinstance(value, User):
                continue
            if value.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Validate password strength
        is_strong, message = AuthenticationService.validate_password_strength(user_data.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {message}"
            )
        
        # Create user
        user_id = f"user_{secrets.token_urlsafe(8)}"
        hashed_password = AuthenticationService.get_password_hash(user_data.password)
        
        user = User(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            company=user_data.company,
            role=user_data.role if user_data.role in ["user", "admin", "viewer"] else "user",
            created_at=datetime.utcnow()
        )
        
        # Store user and password hash separately
        users_db[user_id] = user
        users_db[f"{user_id}_password"] = hashed_password
        
        # Save to persistent storage
        save_users_db(users_db)
        
        logger.info(f"New user created: {user.username} ({user.email})")
        return user
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user with username/password"""
        user = AuthenticationService.get_user_by_username(username)
        if not user:
            return None
        
        stored_password = users_db.get(f"{user.user_id}_password")
        if not stored_password:
            return None
        
        if not AuthenticationService.verify_password(password, stored_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        users_db[user.user_id] = user
        
        # Save to persistent storage
        save_users_db(users_db)
        
        return user
    
    @staticmethod
    def revoke_token(token: str) -> bool:
        """Revoke a token"""
        active_tokens.discard(token)
        return True
    
    @staticmethod
    def revoke_all_user_tokens(user_id: str) -> bool:
        """Revoke all tokens for a user (logout from all devices)"""
        tokens_to_remove = set()
        
        for token in active_tokens:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                if payload.get("user_id") == user_id:
                    tokens_to_remove.add(token)
            except jwt.JWTError:
                tokens_to_remove.add(token)  # Remove invalid tokens
        
        active_tokens.difference_update(tokens_to_remove)
        return True

# Dependency functions for FastAPI
async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current user from JWT token"""
    return AuthenticationService.verify_token(credentials.credentials)

async def get_current_user(token_data: TokenData = Depends(get_current_user_token)) -> User:
    """Get current authenticated user"""
    user = AuthenticationService.get_user(token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# Role-based access control
def require_role(required_roles: list[str]):
    """Decorator for role-based access control"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {required_roles}"
            )
        return current_user
    return role_checker

# Create default admin user if none exists
def initialize_default_users():
    """Initialize default admin user"""
    if not users_db:  # No users exist
        admin_user_data = UserCreate(
            username="admin",
            email="admin@maritime-assistant.com",
            password="MaritimeAdmin2025!",
            full_name="System Administrator",
            company="Maritime Assistant",
            role="admin"
        )
        
        try:
            admin_user = AuthenticationService.create_user(admin_user_data)
            logger.info(f"Default admin user created: {admin_user.username}")
        except Exception as e:
            logger.error(f"Failed to create default admin user: {e}")

# Initialize on import
initialize_default_users()

# Statistics and monitoring
def get_auth_statistics():
    """Get authentication statistics"""
    active_users = len([u for u in users_db.values() if isinstance(u, User) and u.is_active])
    total_users = len([u for u in users_db.values() if isinstance(u, User)])
    active_sessions = len(active_tokens)
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "active_sessions": active_sessions,
        "admin_users": len([u for u in users_db.values() if isinstance(u, User) and u.role == "admin"]),
        "user_roles": {
            "admin": len([u for u in users_db.values() if isinstance(u, User) and u.role == "admin"]),
            "user": len([u for u in users_db.values() if isinstance(u, User) and u.role == "user"]),
            "viewer": len([u for u in users_db.values() if isinstance(u, User) and u.role == "viewer"])
        }
    }
