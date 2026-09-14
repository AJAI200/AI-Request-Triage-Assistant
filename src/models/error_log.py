import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from src.models.base import Base

class ErrorLog(Base):
    __tablename__ = "error_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    function_name = Column(String, nullable=False)
    line_number = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    process_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
