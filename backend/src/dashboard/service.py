from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.dashboard.schemas import (
    AgentDealLeaderboardItem,
    AgentPointsLeaderboardItem,
    AgentRatingLeaderboardItem,
    PlatformOverviewResponse,
)
from src.models import Agent, ReputationRecord, Task
from src.task.schemas import TaskStatusEnum


def get_platform_overview(db: Session) -> PlatformOverviewResponse:
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    total_agents = db.scalar(select(func.count(Agent.id)).where(Agent.is_del.is_(False))) or 0
    total_tasks = db.scalar(select(func.count(Task.id))) or 0
    total_completed_tasks = db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatusEnum.COMPLETED.value)) or 0
    total_open_tasks = db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatusEnum.OPEN.value)) or 0
    total_in_progress_tasks = db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatusEnum.IN_PROGRESS.value)) or 0
    total_submitted_tasks = db.scalar(select(func.count(Task.id)).where(Task.status == TaskStatusEnum.SUBMITTED.value)) or 0
    total_points_supply = db.scalar(select(func.sum(Agent.points)).where(Agent.is_del.is_(False))) or 0
    total_transferred_points = db.scalar(select(func.sum(ReputationRecord.points_transferred))) or 0
    tasks_created_last_24h = db.scalar(select(func.count(Task.id)).where(Task.created_at >= last_24h)) or 0
    tasks_created_last_7d = db.scalar(select(func.count(Task.id)).where(Task.created_at >= last_7d)) or 0
    tasks_completed_last_24h = db.scalar(select(func.count(ReputationRecord.id)).where(ReputationRecord.completed_at >= last_24h)) or 0
    tasks_completed_last_7d = db.scalar(select(func.count(ReputationRecord.id)).where(ReputationRecord.completed_at >= last_7d)) or 0

    return PlatformOverviewResponse(
        total_agents=int(total_agents),
        total_tasks=int(total_tasks),
        total_completed_tasks=int(total_completed_tasks),
        total_open_tasks=int(total_open_tasks),
        total_in_progress_tasks=int(total_in_progress_tasks),
        total_submitted_tasks=int(total_submitted_tasks),
        total_points_supply=int(total_points_supply),
        total_transferred_points=int(total_transferred_points),
        tasks_created_last_24h=int(tasks_created_last_24h),
        tasks_created_last_7d=int(tasks_created_last_7d),
        tasks_completed_last_24h=int(tasks_completed_last_24h),
        tasks_completed_last_7d=int(tasks_completed_last_7d),
    )


def get_agent_points_leaderboard(db: Session, limit: int = 20) -> list[AgentPointsLeaderboardItem]:
    agents = db.execute(
        select(Agent.id, Agent.username, Agent.points)
        .where(Agent.is_del.is_(False))
        .order_by(Agent.points.desc(), Agent.id.asc())
        .limit(limit)
    ).all()
    return [AgentPointsLeaderboardItem(agent_id=item[0], username=item[1], points=item[2]) for item in agents]


def get_agent_rating_leaderboard(db: Session, limit: int = 20) -> list[AgentRatingLeaderboardItem]:
    rows = db.execute(
        select(
            Agent.id,
            Agent.username,
            func.avg(ReputationRecord.rating).label("average_rating"),
            func.count(ReputationRecord.id).label("completed_tasks"),
        )
        .join(ReputationRecord, ReputationRecord.worker_id == Agent.id)
        .where(Agent.is_del.is_(False))
        .group_by(Agent.id, Agent.username)
        .order_by(func.avg(ReputationRecord.rating).desc(), func.count(ReputationRecord.id).desc(), Agent.id.asc())
        .limit(limit)
    ).all()
    return [
        AgentRatingLeaderboardItem(
            agent_id=row[0],
            username=row[1],
            average_rating=float(row[2] or 0.0),
            completed_tasks=int(row[3] or 0),
        )
        for row in rows
    ]


def get_agent_deal_leaderboard(db: Session, limit: int = 20) -> list[AgentDealLeaderboardItem]:
    rows = db.execute(
        select(
            Agent.id,
            Agent.username,
            func.count(ReputationRecord.id).label("completed_tasks"),
            func.sum(ReputationRecord.points_transferred).label("total_earned_points"),
        )
        .join(ReputationRecord, ReputationRecord.worker_id == Agent.id)
        .where(Agent.is_del.is_(False))
        .group_by(Agent.id, Agent.username)
        .order_by(func.count(ReputationRecord.id).desc(), func.sum(ReputationRecord.points_transferred).desc(), Agent.id.asc())
        .limit(limit)
    ).all()
    return [
        AgentDealLeaderboardItem(
            agent_id=row[0],
            username=row[1],
            completed_tasks=int(row[2] or 0),
            total_earned_points=int(row[3] or 0),
        )
        for row in rows
    ]
