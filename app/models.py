import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class ImageStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(SQLEnum(UserTier), default=UserTier.FREE, nullable=False)
    tier_expires_at = Column(DateTime, nullable=True)
    premium_expires_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    images = relationship("Image", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Image(Base):
    __tablename__ = "images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    is_anonymous = Column(Integer, default=0, nullable=False)
    original_path = Column(String(500), nullable=False)
    result_path = Column(String(500), nullable=True)
    status = Column(SQLEnum(ImageStatus), default=ImageStatus.QUEUED, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="images")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    mercado_pago_id = Column(String(255), nullable=True, unique=True)
    plan = Column(String(50), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="payments")
