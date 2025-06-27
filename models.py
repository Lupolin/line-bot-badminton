from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

Base = declarative_base()

class Reply(Base):
    __tablename__ = 'replies'
    id = Column(Integer, primary_key=True)
    group_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    user_name = Column(String)
    reply = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)