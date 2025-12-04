# app/core/user_store.py

import uuid
from app.core.redis_client import redis_client
from app.core.auth_utils import hash_password, verify_password

def create_user(username: str, password: str):
    """ 
    Create user and storee:
    user: <user_id> with {username, passsword}
    And a lookup: username:<username> = user_id
    """
    # check username already exists
    if redis_client.exists(f"username:{username}"):
        return None, "Username already exists"
    
    user_id = str(uuid.uuid4())
    redis_client.hset(f"user:{user_id}", mapping={
        "username": username,
        "password": hash_password(password)
    })
    
    redis_client.set(f"username:{username}", user_id)
    return user_id, None

def authenticate_user(username: str, password: str):
    """
    Check if username exists and password matches.
    """
    user_id = redis_client.get(f"username:{username}")
    
    if not user_id:
        return None, "User Not found"
    
    data = redis_client.hgetall(f"user:{user_id}")
    if not verify_password(password, data["password"]):
        return None, "Incorrect password"
    
    return user_id, None