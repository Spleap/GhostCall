from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.constants import ACCESS_TOKEN_TYPE
from src.auth.exceptions import AuthFailedException
from src.auth.schemas import AuthTokenData, LoginRequest, RegisterRequest
from src.auth.utils import create_access_token, hash_password, verify_password
from src.exceptions import BusinessException
from src.models import Agent


def register_agent(params: RegisterRequest, db: Session) -> Agent:
    exists_agent = db.scalar(select(Agent).where(Agent.username == params.username, Agent.is_del.is_(False)))
    if exists_agent:
        raise BusinessException(code=40001, message="用户名已存在")
    agent = Agent(username=params.username, password_hash=hash_password(params.password), points=1000)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def login_agent(params: LoginRequest, db: Session) -> AuthTokenData:
    agent = db.scalar(select(Agent).where(Agent.username == params.username, Agent.is_del.is_(False)))
    if not agent:
        raise AuthFailedException()
    if not verify_password(params.password, agent.password_hash):
        raise AuthFailedException()
    token = create_access_token(agent_id=agent.id, username=agent.username)
    return AuthTokenData(access_token=token, token_type=ACCESS_TOKEN_TYPE)
