import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.auth.utils import decode_access_token
from src.database import get_db
from src.models import Agent


security = HTTPBearer(auto_error=False)


def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Agent:
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail="令牌无效") from error
    agent_id = int(payload["sub"])
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.is_del.is_(False)).first()
    if not agent:
        raise HTTPException(status_code=401, detail="用户不存在")
    return agent
