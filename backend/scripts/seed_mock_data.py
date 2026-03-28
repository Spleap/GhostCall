import hashlib
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database import Base, SessionLocal, engine
from src.models import Agent, ReputationRecord, Task
from src.task.schemas import TaskStatusEnum


RANDOM_SEED = 20260328
AGENT_COUNT = 160
COMPLETED_TASK_COUNT = 960
OPEN_TASK_COUNT = 180
IN_PROGRESS_TASK_COUNT = 110
SUBMITTED_TASK_COUNT = 90


def hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def random_time_in_days(days: int) -> datetime:
    now = datetime.utcnow()
    return now - timedelta(seconds=random.randint(0, days * 24 * 3600))


def choose_task_profile() -> tuple[str, str, int]:
    profiles = [
        ("数据抓取", "需要抓取目标站点并输出结构化JSON", 40, 220),
        ("网页自动化", "完成浏览器自动化流程并返回执行结果", 60, 280),
        ("文本摘要", "对给定材料生成可读摘要和结论", 30, 160),
        ("代码修复", "修复指定仓库中的问题并给出说明", 90, 420),
        ("API联调", "对第三方接口进行联调并输出日志", 70, 260),
        ("Prompt优化", "针对业务场景优化提示词效果", 50, 200),
        ("报表生成", "生成日报周报并附关键指标分析", 45, 180),
        ("知识检索", "完成资料检索并整理可复用结论", 35, 150),
        ("翻译润色", "中英文互译并保证术语统一", 25, 120),
        ("测试编写", "补充自动化测试并输出覆盖率", 80, 300),
    ]
    name, description, low, high = random.choice(profiles)
    reward = random.randint(low, high)
    return name, description, reward


def make_agents() -> list[Agent]:
    prefixes = ["alpha", "nova", "quant", "byte", "flux", "echo", "zen", "atlas", "vector", "neon"]
    domains = ["crawler", "analyst", "builder", "solver", "scribe", "runner", "pilot", "maker", "guard", "spark"]
    agents: list[Agent] = []
    for idx in range(AGENT_COUNT):
        username = f"{random.choice(prefixes)}_{random.choice(domains)}_{idx:03d}"
        points = random.randint(1400, 5200)
        agent = Agent(
            username=username,
            password_hash=hash_password("pass1234"),
            points=points,
            is_del=False,
            created_at=random_time_in_days(220),
        )
        agent.role_bias = random.uniform(0.3, 0.95)
        agent.quality = random.uniform(0.35, 0.98)
        agents.append(agent)
    return agents


def pick_employer(agents: list[Agent], min_points: int) -> Agent:
    pool = [a for a in agents if a.points >= min_points]
    if not pool:
        candidate = random.choice(agents)
        candidate.points += min_points + random.randint(200, 800)
        return candidate
    weights = [a.role_bias for a in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def pick_worker(agents: list[Agent], employer_id: int) -> Agent:
    pool = [a for a in agents if a.id != employer_id]
    weights = [a.quality for a in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def build_rating(worker_quality: float) -> int:
    expected = 4.2 + worker_quality * 5.4
    value = int(round(random.gauss(expected, 1.3)))
    return max(0, min(10, value))


def build_comment(score: int) -> str:
    good = ["响应快，结果可直接上线", "交付质量高，沟通顺畅", "完成度很高，细节处理优秀", "数据准确，文档清晰"]
    normal = ["按要求完成，整体可用", "结果符合预期，少量可优化", "质量稳定，交付及时", "可用但仍有改进空间"]
    bad = ["结果偏差较大，需要返工", "沟通成本偏高，延期提交", "缺少关键产物，未完全达标", "质量一般，建议加强验证"]
    if score >= 8:
        return random.choice(good)
    if score >= 5:
        return random.choice(normal)
    return random.choice(bad)


def create_completed_task(agents: list[Agent], session: SessionLocal) -> None:
    title, description, reward = choose_task_profile()
    employer = pick_employer(agents, reward + 120)
    worker = pick_worker(agents, employer.id)
    created_at = random_time_in_days(45)
    completed_at = created_at + timedelta(minutes=random.randint(30, 60 * 72))
    now = datetime.utcnow()
    if completed_at > now:
        completed_at = now - timedelta(minutes=random.randint(3, 30))
    task = Task(
        employer_id=employer.id,
        worker_id=worker.id,
        title=title,
        description=description,
        reward_points=reward,
        status=TaskStatusEnum.COMPLETED.value,
        result_payload='{"status":"ok","confidence":0.91}',
        created_at=created_at,
        updated_at=completed_at,
    )
    session.add(task)
    session.flush()
    rating = build_rating(worker.quality)
    record = ReputationRecord(
        task_id=task.id,
        employer_id=employer.id,
        worker_id=worker.id,
        points_transferred=reward,
        rating=rating,
        comment=build_comment(rating),
        completed_at=completed_at,
    )
    employer.points -= reward
    worker.points += reward
    session.add(record)


def create_unfinished_task(status: TaskStatusEnum, agents: list[Agent], session: SessionLocal) -> None:
    title, description, reward = choose_task_profile()
    employer = pick_employer(agents, max(reward, 80))
    created_at = random_time_in_days(25)
    updated_at = created_at + timedelta(minutes=random.randint(10, 60 * 24))
    if status == TaskStatusEnum.OPEN:
        task = Task(
            employer_id=employer.id,
            worker_id=None,
            title=title,
            description=description,
            reward_points=reward,
            status=TaskStatusEnum.OPEN.value,
            result_payload=None,
            created_at=created_at,
            updated_at=updated_at,
        )
        session.add(task)
        return
    worker = pick_worker(agents, employer.id)
    result_payload = None
    if status == TaskStatusEnum.SUBMITTED:
        result_payload = '{"preview":"result attached","version":"v2"}'
    task = Task(
        employer_id=employer.id,
        worker_id=worker.id,
        title=title,
        description=description,
        reward_points=reward,
        status=status.value,
        result_payload=result_payload,
        created_at=created_at,
        updated_at=updated_at,
    )
    session.add(task)


def seed() -> None:
    random.seed(RANDOM_SEED)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        session.query(ReputationRecord).delete()
        session.query(Task).delete()
        session.query(Agent).delete()
        session.commit()

        agents = make_agents()
        session.add_all(agents)
        session.flush()

        for _ in range(COMPLETED_TASK_COUNT):
            create_completed_task(agents=agents, session=session)
        for _ in range(OPEN_TASK_COUNT):
            create_unfinished_task(status=TaskStatusEnum.OPEN, agents=agents, session=session)
        for _ in range(IN_PROGRESS_TASK_COUNT):
            create_unfinished_task(status=TaskStatusEnum.IN_PROGRESS, agents=agents, session=session)
        for _ in range(SUBMITTED_TASK_COUNT):
            create_unfinished_task(status=TaskStatusEnum.SUBMITTED, agents=agents, session=session)

        session.commit()

        total_agents = session.scalar(select(func.count(Agent.id)).where(Agent.is_del.is_(False))) or 0
        total_tasks = session.scalar(select(func.count(Task.id))) or 0
        total_records = session.scalar(select(func.count(ReputationRecord.id))) or 0
        avg_rating = session.scalar(select(func.avg(ReputationRecord.rating))) or 0
        sum_points = session.scalar(select(func.sum(Agent.points)).where(Agent.is_del.is_(False))) or 0
        rows = session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status).order_by(Task.status.asc())
        ).all()
        print(f"agents={int(total_agents)} tasks={int(total_tasks)} records={int(total_records)}")
        print(f"avg_rating={float(avg_rating):.2f} total_points_supply={int(sum_points)}")
        print("status_distribution=" + ", ".join([f"{row[0]}:{int(row[1])}" for row in rows]))
    finally:
        session.close()


if __name__ == "__main__":
    seed()
