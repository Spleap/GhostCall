from sqlalchemy import select
from sqlalchemy.orm import Session

from src.exceptions import BusinessException
from src.models import Agent, ReputationRecord, Task
from src.task.schemas import CreateTaskRequest, RateTaskRequest, SubmitTaskRequest, TaskStatusEnum


def create_task(params: CreateTaskRequest, employer: Agent, db: Session) -> Task:
    task = Task(
        employer_id=employer.id,
        title=params.title,
        description=params.description,
        reward_points=params.reward_points,
        status=TaskStatusEnum.OPEN.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_open_tasks(db: Session) -> list[Task]:
    return db.scalars(select(Task).where(Task.status == TaskStatusEnum.OPEN.value).order_by(Task.created_at.desc())).all()


def accept_task(task_id: int, worker: Agent, db: Session) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise BusinessException(code=40401, message="任务不存在")
    if task.status != TaskStatusEnum.OPEN.value:
        raise BusinessException(code=40021, message="任务不可接单")
    if task.employer_id == worker.id:
        raise BusinessException(code=40022, message="不能接自己发布的任务")
    task.worker_id = worker.id
    task.status = TaskStatusEnum.IN_PROGRESS.value
    db.commit()
    db.refresh(task)
    return task


def submit_task(task_id: int, params: SubmitTaskRequest, worker: Agent, db: Session) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise BusinessException(code=40401, message="任务不存在")
    if task.worker_id != worker.id:
        raise BusinessException(code=40321, message="仅接单者可提交结果")
    if task.status != TaskStatusEnum.IN_PROGRESS.value:
        raise BusinessException(code=40023, message="任务状态不允许提交")
    task.result_payload = params.result_payload
    task.status = TaskStatusEnum.SUBMITTED.value
    db.commit()
    db.refresh(task)
    return task


def rate_task(task_id: int, params: RateTaskRequest, employer: Agent, db: Session) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise BusinessException(code=40401, message="任务不存在")
    if task.employer_id != employer.id:
        raise BusinessException(code=40322, message="仅发布者可评分")
    if task.status != TaskStatusEnum.SUBMITTED.value:
        raise BusinessException(code=40024, message="任务尚未提交结果")
    if task.worker_id is None:
        raise BusinessException(code=40025, message="任务尚未被接单")
    worker = db.scalar(select(Agent).where(Agent.id == task.worker_id, Agent.is_del.is_(False)))
    if not worker:
        raise BusinessException(code=40402, message="接单者不存在")
    if employer.points < task.reward_points:
        raise BusinessException(code=40026, message="积分不足")

    existed_record = db.scalar(select(ReputationRecord).where(ReputationRecord.task_id == task.id))
    if existed_record:
        raise BusinessException(code=40027, message="任务已评分")

    employer.points -= task.reward_points
    worker.points += task.reward_points

    record = ReputationRecord(
        task_id=task.id,
        employer_id=employer.id,
        worker_id=worker.id,
        points_transferred=task.reward_points,
        rating=params.rating,
        comment=params.comment,
    )
    task.status = TaskStatusEnum.COMPLETED.value
    db.add(record)
    db.commit()
    db.refresh(task)
    return task
