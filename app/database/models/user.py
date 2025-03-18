from sqlalchemy import Boolean, Column, String, ForeignKey, DateTime, Text
from datetime import datetime
import uuid
from .base import Base
from sqlalchemy.orm import relationship
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    hashed_password = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    accounts = relationship("Account", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True,
                default=lambda: str(uuid.uuid4()), index=True)
    # Changed from Integer to String(36)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    provider = Column(String)
    provider_account_id = Column(String)
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    # JSON string of the full token response
    token_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="accounts")

    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            'user_id', 'provider', name='uix_user_provider'),
    )
