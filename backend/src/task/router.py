from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_agent
from src.database import get_db
from src.models import Agent
from src.schemas import BaseResponse
from src.task.schemas import CreateTaskRequest, RateTaskRequest, SubmitTaskRequest, TaskResponse
from src.task.service import accept_task, create_task, list_open_tasks, rate_task, submit_task


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    name="发布任务",
    response_model=BaseResponse[TaskResponse],
    responses={200: {"description": "成功"}},
)
def create_task_api(
    params: CreateTaskRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BaseResponse[TaskResponse]:
    task = create_task(params=params, employer=current_agent, db=db)
    return BaseResponse(data=TaskResponse.model_validate(task))


@router.get(
    "/open",
    name="查询待接任务",
    response_model=BaseResponse[list[TaskResponse]],
    responses={200: {"description": "成功"}},
)
def list_open_tasks_api(db: Session = Depends(get_db)) -> BaseResponse[list[TaskResponse]]:
    tasks = list_open_tasks(db=db)
    return BaseResponse(data=[TaskResponse.model_validate(item) for item in tasks])


@router.post(
    "/{task_id}/accept",
    name="接单",
    response_model=BaseResponse[TaskResponse],
    responses={200: {"description": "成功"}},
)
def accept_task_api(
    task_id: int,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BaseResponse[TaskResponse]:
    task = accept_task(task_id=task_id, worker=current_agent, db=db)
    return BaseResponse(data=TaskResponse.model_validate(task))


@router.post(
    "/{task_id}/submit",
    name="提交任务结果",
    response_model=BaseResponse[TaskResponse],
    responses={200: {"description": "成功"}},
)
def submit_task_api(
    task_id: int,
    params: SubmitTaskRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BaseResponse[TaskResponse]:
    task = submit_task(task_id=task_id, params=params, worker=current_agent, db=db)
    return BaseResponse(data=TaskResponse.model_validate(task))


@router.post(
    "/{task_id}/rate",
    name="评分并结算",
    response_model=BaseResponse[TaskResponse],
    responses={200: {"description": "成功"}},
)
def rate_task_api(
    task_id: int,
    params: RateTaskRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> BaseResponse[TaskResponse]:
    task = rate_task(task_id=task_id, params=params, employer=current_agent, db=db)
    return BaseResponse(data=TaskResponse.model_validate(task))
