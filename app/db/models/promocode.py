from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from db.base import Base

class Promocode(Base):
    __tablename__ = "promocodes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    discount = Column(Float, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)