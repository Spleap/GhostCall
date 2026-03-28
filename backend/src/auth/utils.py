import hashlib
from datetime import datetime, timedelta, timezone

import jwt

from src.auth.config import jwt_algorithm, jwt_expire_minutes, jwt_secret_key


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def verify_password(raw_password: str, password_hash: str) -> bool:
    return hash_password(raw_password) == password_hash


def create_access_token(agent_id: int, username: str) -> str:
    expire_at = datetime.now(tz=timezone.utc) + timedelta(minutes=jwt_expire_minutes)
    payload = {
        "sub": str(agent_id),
        "username": username,
        "exp": expire_at,
    }
    return jwt.encode(payload, jwt_secret_key, algorithm=jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, jwt_secret_key, algorithms=[jwt_algorithm])
