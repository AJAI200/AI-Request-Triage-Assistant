from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base

class ResponseDraft(Base):
    __tablename__ = "response_draft"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("request.id"), unique=True, nullable=False)
    draft_text = Column(Text, nullable=False)
    final_text = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    request = relationship("Request", back_populates="draft")
