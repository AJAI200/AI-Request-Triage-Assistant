from sqlalchemy import Column, Integer, String
from src.models.base import Base

class Owner(Base):
    __tablename__ = "owner"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
