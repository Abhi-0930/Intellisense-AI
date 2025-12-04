from fastapi import APIRouter, Header, HTTPException

from pydantic import BaseModel

from app.core.auth_utils import create_jwt_token, decode_jwt_token
from app.core.user_store import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupRequest(BaseModel):
    username: str
    password: str
    
class LoginRequest(BaseModel):
    username: str
    password: str
    
class AuthResponse(BaseModel):
    user_id: str
    username: str
    token: str
    
@router.post("/signup", response_model=AuthResponse)
async def signup(payload: SignupRequest):
    user_id, error = create_user(payload.username, payload.password)
    if error:
        raise HTTPException(400, detail= error)
    
    token = create_jwt_token(user_id, payload.username)
    
    return AuthResponse(
        user_id=user_id,
        username=payload.username,
        token=token
    )
    
@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    user_id, error = authenticate_user(payload.username, payload.password)
    if error: 
        raise HTTPException(400, error)
    
    token = create_jwt_token(user_id, payload.username)
    
    return AuthResponse(
        user_id = user_id,
        username = payload.username,
        token = token
    )
    
@router.get("/me")
async def get_me(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    
    token = authorization.replace("Bearer ", "")
    decoded = decode_jwt_token(token)
    
    if not decoded:
        raise HTTPException(401, "Invalid token")
    
    return decoded