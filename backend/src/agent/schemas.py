from pydantic import BaseModel, Field


class AgentProfileResponse(BaseModel):
    id: int = Field(..., description="Agent ID")
    username: str = Field(..., description="用户名")
    points: int = Field(..., description="当前积分")


class ReputationRecordResponse(BaseModel):
    task_id: int = Field(..., description="任务ID")
    points_transferred: int = Field(..., description="交易积分")
    rating: int = Field(..., ge=0, le=10, description="评分")
    comment: str | None = Field(default=None, description="评价内容")
    completed_at: str = Field(..., description="完成时间")


class ReputationSummaryResponse(BaseModel):
    total_completed_tasks: int = Field(..., description="完成任务数")
    average_rating: float = Field(..., description="平均评分")
