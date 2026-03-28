from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    points: Mapped[int] = mapped_column(Integer, default=0)
    is_del: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    posted_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="employer",
        foreign_keys="Task.employer_id",
    )
    accepted_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="worker",
        foreign_keys="Task.worker_id",
    )
    received_reputations: Mapped[list["ReputationRecord"]] = relationship(
        "ReputationRecord",
        back_populates="worker",
        foreign_keys="ReputationRecord.worker_id",
        cascade="all, delete-orphan",
    )
    sent_reputations: Mapped[list["ReputationRecord"]] = relationship(
        "ReputationRecord",
        back_populates="employer",
        foreign_keys="ReputationRecord.employer_id",
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    worker_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    reward_points: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    result_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    employer: Mapped["Agent"] = relationship("Agent", back_populates="posted_tasks", foreign_keys=[employer_id])
    worker: Mapped["Agent | None"] = relationship("Agent", back_populates="accepted_tasks", foreign_keys=[worker_id])
    reputation: Mapped["ReputationRecord | None"] = relationship(
        "ReputationRecord",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ReputationRecord(Base):
    __tablename__ = "reputation_records"
    __table_args__ = (UniqueConstraint("task_id", name="uq_reputation_task_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    points_transferred: Mapped[int] = mapped_column(Integer)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["Task"] = relationship("Task", back_populates="reputation")
    employer: Mapped["Agent"] = relationship("Agent", back_populates="sent_reputations", foreign_keys=[employer_id])
    worker: Mapped["Agent"] = relationship("Agent", back_populates="received_reputations", foreign_keys=[worker_id])
