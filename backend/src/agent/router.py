from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.agent.schemas import AgentProfileResponse, ReputationRecordResponse, ReputationSummaryResponse
from src.agent.service import get_agent_profile, get_reputation_records, get_reputation_summary
from src.auth.dependencies import get_current_agent
from src.database import get_db
from src.models import Agent
from src.schemas import BaseResponse


router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get(
    "/me",
    name="获取当前Agent资料",
    response_model=BaseResponse[AgentProfileResponse],
    responses={200: {"description": "成功"}},
)
def get_me(current_agent: Agent = Depends(get_current_agent)) -> BaseResponse[AgentProfileResponse]:
    return BaseResponse(data=get_agent_profile(current_agent))


@router.get(
    "/me/reputation-records",
    name="获取当前Agent信誉记录",
    response_model=BaseResponse[list[ReputationRecordResponse]],
    responses={200: {"description": "成功"}},
)
def get_my_reputation_records(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BaseResponse[list[ReputationRecordResponse]]:
    return BaseResponse(data=get_reputation_records(agent_id=current_agent.id, db=db))


@router.get(
    "/me/reputation-summary",
    name="获取当前Agent信誉汇总",
    response_model=BaseResponse[ReputationSummaryResponse],
    responses={200: {"description": "成功"}},
)
def get_my_reputation_summary(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BaseResponse[ReputationSummaryResponse]:
    return BaseResponse(data=get_reputation_summary(agent_id=current_agent.id, db=db))
