from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.schemas import AgentPublic, AuthTokenData, LoginRequest, RegisterRequest
from src.auth.service import login_agent, register_agent
from src.database import get_db
from src.schemas import BaseResponse


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    name="注册账号",
    response_model=BaseResponse[AgentPublic],
    responses={200: {"description": "成功"}},
)
def register(params: RegisterRequest, db: Session = Depends(get_db)) -> BaseResponse[AgentPublic]:
    agent = register_agent(params=params, db=db)
    return BaseResponse(data=AgentPublic.model_validate(agent))


@router.post(
    "/login",
    name="登录",
    response_model=BaseResponse[AuthTokenData],
    responses={200: {"description": "成功"}},
)
def login(params: LoginRequest, db: Session = Depends(get_db)) -> BaseResponse[AuthTokenData]:
    token_data = login_agent(params=params, db=db)
    return BaseResponse(data=token_data)
