from sqlalchemy import Boolean, Column, String, TIMESTAMP, Integer, ForeignKey, DateTime
from datetime import datetime, timezone
import uuid
from .base import Base
from sqlalchemy.orm import relationship
import sqlalchemy

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    profile_image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with Account
    accounts = relationship("Account", back_populates="user")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    provider = Column(String)  # "google", "github", etc.
    provider_account_id = Column(String)  # ID from the provider

    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with User
    user = relationship("User", back_populates="accounts")

    __table_args__ = (
        # Ensure one account per provider per user
        sqlalchemy.UniqueConstraint('user_id', 'provider', name='uix_user_provider'),
    )
