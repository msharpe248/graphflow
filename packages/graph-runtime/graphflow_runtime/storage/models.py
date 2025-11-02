"""Database models for GraphFlow Runtime."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Agent(Base):
    """Stored agent definition."""

    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    framework = Column(String, nullable=False)  # pydantic_ai | langgraph
    graph_definition = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    runs = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, framework={self.framework})>"


class AgentRun(Base):
    """Agent execution run."""

    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    status = Column(String, nullable=False, index=True)  # pending|running|completed|failed|stopped
    inputs = Column(JSON, nullable=False)
    outputs = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="runs")

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, agent_id={self.agent_id}, status={self.status})>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get run duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
