import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from src.models.base import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_template"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    template_text = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
