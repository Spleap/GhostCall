from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="账号")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="账号")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class AuthTokenData(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")


class AgentPublic(BaseModel):
    id: int
    username: str
    points: int
    model_config = ConfigDict(from_attributes=True)
