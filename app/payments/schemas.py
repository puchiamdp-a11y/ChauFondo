from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreatePaymentRequest(BaseModel):
    """Request to create a payment preference."""
    plan: str = Field(..., description="Plan type: premium_month or premium_year")


class PaymentResponse(BaseModel):
    """Payment preference response."""
    payment_id: str = Field(..., description="Mercado Pago preference ID")
    checkout_url: str = Field(..., description="URL for user to complete payment")
    status: str = Field(default="pending", description="Payment status")
    expires_at: datetime = Field(..., description="Preference expiration time")


class PaymentStatusResponse(BaseModel):
    """Payment status response."""
    payment_id: str
    status: str
    amount: float
    plan: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    tier_expires_at: Optional[datetime] = None


class WebhookPayload(BaseModel):
    """Mercado Pago webhook payload."""
    action: str
    type: str
    data: dict
    api_version: str

    class Config:
        extra = "allow"
