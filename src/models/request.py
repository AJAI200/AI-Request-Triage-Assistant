import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import relationship
from src.models.base import Base

class Request(Base):
    __tablename__ = "request"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raw_text = Column(Text, nullable=False)
    channel = Column(String, nullable=True)
    status = Column(String, nullable=False, default="new")  # new | classified | needs_review
    process_time_ms = Column(Float, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    received_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    classification = relationship("Classification", uselist=False, back_populates="request", cascade="all, delete-orphan")
    draft = relationship("ResponseDraft", uselist=False, back_populates="request", cascade="all, delete-orphan")
