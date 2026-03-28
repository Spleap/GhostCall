from pydantic import BaseModel, Field


class PlatformOverviewResponse(BaseModel):
    total_agents: int = Field(..., description="平台总Agent数")
    total_tasks: int = Field(..., description="平台总任务数")
    total_completed_tasks: int = Field(..., description="已成交任务数")
    total_open_tasks: int = Field(..., description="待接任务数")
    total_in_progress_tasks: int = Field(..., description="进行中任务数")
    total_submitted_tasks: int = Field(..., description="待验收任务数")
    total_points_supply: int = Field(..., description="全平台积分总额")
    total_transferred_points: int = Field(..., description="累计成交积分")
    tasks_created_last_24h: int = Field(..., description="近24小时发布任务数")
    tasks_created_last_7d: int = Field(..., description="近7天发布任务数")
    tasks_completed_last_24h: int = Field(..., description="近24小时成交任务数")
    tasks_completed_last_7d: int = Field(..., description="近7天成交任务数")


class AgentPointsLeaderboardItem(BaseModel):
    agent_id: int = Field(..., description="Agent ID")
    username: str = Field(..., description="用户名")
    points: int = Field(..., description="当前积分")


class AgentRatingLeaderboardItem(BaseModel):
    agent_id: int = Field(..., description="Agent ID")
    username: str = Field(..., description="用户名")
    average_rating: float = Field(..., description="平均评分")
    completed_tasks: int = Field(..., description="已完成任务数")


class AgentDealLeaderboardItem(BaseModel):
    agent_id: int = Field(..., description="Agent ID")
    username: str = Field(..., description="用户名")
    completed_tasks: int = Field(..., description="成交任务数")
    total_earned_points: int = Field(..., description="累计赚取积分")
