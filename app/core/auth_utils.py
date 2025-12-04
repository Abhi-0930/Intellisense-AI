# app/core/auth_utils.py
import os
import time
import jwt
import bcrypt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7 # 7 days

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed:str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_jwt_token(user_id: str, username: str):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS
    }
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None