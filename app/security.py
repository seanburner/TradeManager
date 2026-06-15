from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import hmac  # <--- ADD THIS IMPORT HERE
#from passlib.context import CryptContext
from app.config import settings

# Setup bcrypt for password hashing
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plain text password by hashing it with SHA-256 
    and verifying it against the hex string stored in MariaDB.
    """
    # Compute the SHA-256 hex digest of the incoming string
    incoming_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    
    # Use hmac.compare_digest to protect against timing attacks
    return hmac.compare_digest(incoming_hash, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a standard SHA-256 hex digest of a password string."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generates a secure JSON Web Token (JWT) signed with our SECRET_KEY."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt
