# app/api/routes/session.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import time
import uuid

from app.core.redis_client import redis_client

router = APIRouter(
    prefix="/session",
    tags = ["Session Managerr"]
)

SESSION_TTL_SECONDS = 60 * 60 * 24 # 24 hours in seconds

class CreateSessionRequest(BaseModel):
    user_id: str
    
class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str
    expires_in_seconds: int 
    
@router.post("/create", response_model=CreateSessionResponse)
async def create_session(payload: CreateSessionRequest) -> CreateSessionResponse:
    """
    1. Take user_id from the frontend
    2. Generate a random session_id(UUID 4)
    3. store it in redis with 24 hour expiry
    4. Return session_id to frontend
    """
    if not payload.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"
    
    value = {
        "user_id" : payload.user_id,
        "created_at" : int(time.time())
    }
    
    # Save as hash
    redis_client.hset(key, mapping=value)
    # Set expiry (24 hours)
    redis_client.expire(key, SESSION_TTL_SECONDS)
    
    return CreateSessionResponse(
        session_id=session_id,
        user_id=payload.user_id,
        expires_in_seconds=SESSION_TTL_SECONDS
    )