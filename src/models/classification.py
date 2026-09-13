import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base

class Classification(Base):
    __tablename__ = "classification"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("request.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)
    priority = Column(String, nullable=False)  # Low | Medium | High | Urgent
    priority_reason = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("owner.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    request = relationship("Request", back_populates="classification")
    category = relationship("Category")
    owner = relationship("Owner")
