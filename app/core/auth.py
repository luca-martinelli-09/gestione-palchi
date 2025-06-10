import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, Optional

import redis
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.database.base import get_db
from app.models.auth import User, UserRole

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Redis cache for token blacklist and user sessions (optional)
# In production, configure Redis connection
try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    redis_available = redis_client.ping()
except:
    redis_client = None
    redis_available = False


class AuthService:
    """Optimized authentication service with caching."""

    def __init__(self, settings: Settings = None):
        self.settings = settings or get_settings()
        self.pwd_context = pwd_context

    @lru_cache(maxsize=1000)
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash (cached)."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode, self.settings.secret_key, algorithm=self.settings.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify a JWT token and return the payload."""
        try:
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                return None

            payload = jwt.decode(
                token, self.settings.secret_key, algorithms=[self.settings.algorithm]
            )

            # Validate token type
            if payload.get("type") != "access":
                return None

            return payload

        except JWTError:
            return None

    def authenticate_user(
        self, db: Session, username: str, password: str
    ) -> Optional[User]:
        """Authenticate a user with username and password."""
        # Try to get from cache first
        user_cache_key = f"user:{username}"
        cached_user = self._get_from_cache(user_cache_key)

        if cached_user:
            user = User(**cached_user)
        else:
            user = db.query(User).filter(User.username == username).first()
            if user:
                # Cache user data (without password)
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "role": user.role.value if user.role else "viewer",
                    "hashed_password": user.hashed_password,
                }
                self._set_cache(user_cache_key, user_data, expire=300)  # 5 minutes

        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        return user

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username with caching."""
        user_cache_key = f"user:{username}"
        cached_user = self._get_from_cache(user_cache_key)

        if cached_user:
            return User(**cached_user)

        user = db.query(User).filter(User.username == username).first()
        if user:
            # Cache user data
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "role": user.role.value if user.role else "viewer",
                "hashed_password": user.hashed_password,
            }
            self._set_cache(user_cache_key, user_data, expire=300)

        return user

    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist."""
        if not redis_available:
            return False

        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
                options={"verify_exp": False},
            )

            exp = payload.get("exp")
            if exp:
                # Calculate TTL until token expires
                expire_time = datetime.fromtimestamp(exp)
                ttl = int((expire_time - datetime.utcnow()).total_seconds())

                if ttl > 0:
                    redis_client.setex(f"blacklist:{token}", ttl, "1")
                    return True
        except:
            pass

        return False

    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        if not redis_available:
            return False

        try:
            return redis_client.exists(f"blacklist:{token}")
        except:
            return False

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache."""
        if not redis_available:
            return None

        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except:
            pass

        return None

    def _set_cache(self, key: str, data: Dict[str, Any], expire: int = 300) -> bool:
        """Set data in cache."""
        if not redis_available:
            return False

        try:
            redis_client.setex(key, expire, json.dumps(data, default=str))
            return True
        except:
            return False

    def invalidate_user_cache(self, username: str):
        """Invalidate user cache."""
        if redis_available:
            try:
                redis_client.delete(f"user:{username}")
            except:
                pass


# Global auth service instance
auth_service = AuthService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Get the current authenticated user."""
    if not credentials:
        raise AuthenticationException("🔐 Credenziali di autenticazione richieste")

    payload = auth_service.verify_token(credentials.credentials)
    if not payload:
        raise AuthenticationException("❌ Token non valido o scaduto")

    username = payload.get("sub")
    if not username:
        raise AuthenticationException("❌ Payload del token non valido")

    user = auth_service.get_user_by_username(db, username)
    if not user:
        raise AuthenticationException("🔍 Utente non trovato")

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise AuthorizationException("🚫 Account utente disabilitato")

    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current superuser."""
    if not current_user.is_superuser:
        raise AuthorizationException("👑 Privilegi di superutente richiesti")

    return current_user


# Optional authentication for public endpoints
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except AuthenticationException:
        return None


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin or superadmin role."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERADMIN]:
        raise AuthorizationException("🔒 Privilegi di amministratore richiesti")
    return current_user


def require_superadmin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require superadmin role."""
    if current_user.role != UserRole.SUPERADMIN:
        raise AuthorizationException("👑 Privilegi di superamministratore richiesti")
    return current_user


def require_viewer_or_above(current_user: User = Depends(get_current_active_user)) -> User:
    """Require at least viewer role (all authenticated users)."""
    return current_user


# Backward compatibility
get_password_hash = auth_service.get_password_hash
verify_password = auth_service.verify_password
create_access_token = auth_service.create_access_token
authenticate_user = auth_service.authenticate_user
