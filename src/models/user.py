import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.models.base import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="staff")  # admin | staff
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
