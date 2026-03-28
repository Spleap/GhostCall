from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TaskStatusEnum(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: str = Field(default="", description="任务描述")
    reward_points: int = Field(..., gt=0, description="赏金积分")


class SubmitTaskRequest(BaseModel):
    result_payload: str = Field(..., min_length=1, description="任务结果")


class RateTaskRequest(BaseModel):
    rating: int = Field(..., ge=0, le=10, description="评分")
    comment: str | None = Field(default=None, description="评价内容")


class TaskResponse(BaseModel):
    id: int
    employer_id: int
    worker_id: int | None
    title: str
    description: str
    reward_points: int
    status: TaskStatusEnum
    result_payload: str | None

    model_config = ConfigDict(from_attributes=True)
