from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.agent.schemas import AgentProfileResponse, ReputationRecordResponse, ReputationSummaryResponse
from src.models import Agent, ReputationRecord


def get_agent_profile(agent: Agent) -> AgentProfileResponse:
    return AgentProfileResponse(id=agent.id, username=agent.username, points=agent.points)


def get_reputation_records(agent_id: int, db: Session) -> list[ReputationRecordResponse]:
    records = db.scalars(
        select(ReputationRecord)
        .where(ReputationRecord.worker_id == agent_id)
        .order_by(ReputationRecord.completed_at.desc())
    ).all()
    return [
        ReputationRecordResponse(
            task_id=item.task_id,
            points_transferred=item.points_transferred,
            rating=item.rating,
            comment=item.comment,
            completed_at=item.completed_at.isoformat(),
        )
        for item in records
    ]


def get_reputation_summary(agent_id: int, db: Session) -> ReputationSummaryResponse:
    total, avg = db.execute(
        select(func.count(ReputationRecord.id), func.avg(ReputationRecord.rating)).where(ReputationRecord.worker_id == agent_id)
    ).one()
    return ReputationSummaryResponse(total_completed_tasks=int(total or 0), average_rating=float(avg or 0.0))
