from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.dashboard.schemas import (
    AgentDealLeaderboardItem,
    AgentPointsLeaderboardItem,
    AgentRatingLeaderboardItem,
    PlatformOverviewResponse,
)
from src.dashboard.service import (
    get_agent_deal_leaderboard,
    get_agent_points_leaderboard,
    get_agent_rating_leaderboard,
    get_platform_overview,
)
from src.database import get_db
from src.schemas import BaseResponse


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/overview",
    name="获取平台总览",
    response_model=BaseResponse[PlatformOverviewResponse],
    responses={200: {"description": "成功"}},
)
def get_overview(db: Session = Depends(get_db)) -> BaseResponse[PlatformOverviewResponse]:
    return BaseResponse(data=get_platform_overview(db=db))


@router.get(
    "/leaderboards/agent-points",
    name="获取Agent积分排行榜",
    response_model=BaseResponse[list[AgentPointsLeaderboardItem]],
    responses={200: {"description": "成功"}},
)
def get_points_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BaseResponse[list[AgentPointsLeaderboardItem]]:
    return BaseResponse(data=get_agent_points_leaderboard(db=db, limit=limit))


@router.get(
    "/leaderboards/agent-ratings",
    name="获取Agent评分排行榜",
    response_model=BaseResponse[list[AgentRatingLeaderboardItem]],
    responses={200: {"description": "成功"}},
)
def get_rating_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BaseResponse[list[AgentRatingLeaderboardItem]]:
    return BaseResponse(data=get_agent_rating_leaderboard(db=db, limit=limit))


@router.get(
    "/leaderboards/agent-deals",
    name="获取Agent成交任务排行榜",
    response_model=BaseResponse[list[AgentDealLeaderboardItem]],
    responses={200: {"description": "成功"}},
)
def get_deal_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BaseResponse[list[AgentDealLeaderboardItem]]:
    return BaseResponse(data=get_agent_deal_leaderboard(db=db, limit=limit))
