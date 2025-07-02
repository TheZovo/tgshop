from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    balance = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    purchases = relationship("Purchase", back_populates="user")
    payments = relationship("Payment", back_populates="user")