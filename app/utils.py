import hashlib
import jwt
import datetime
from typing import Union, Any
from config import settings

# JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
JWT_SECRET_KEY = settings.JWT_SECRET_KEY


# -------------------------------
# Password Helpers
# -------------------------------
def get_hashed_password(password: str) -> str:
    """Hash plain password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_pass: str) -> bool:
    """Check if password matches hashed version"""
    return get_hashed_password(password) == hashed_pass


# -------------------------------
# JWT Helpers
# -------------------------------
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    """Create JWT access token"""
    if expires_delta is not None:
        expires_delta = datetime.datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """Decode JWT token and handle errors"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        return {"status": "success", "status_code": 200, "data": email}
    except jwt.ExpiredSignatureError:
        return {"status": "error", "status_code": 401, "detail": "Token expired"}
    except jwt.InvalidTokenError:
        return {"status": "error", "status_code": 403, "detail": "Invalid token"}
