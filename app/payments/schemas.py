from pydantic import BaseModel
from typing import Optional


class CreateSubscriptionRequest(BaseModel):
    plan: str = "premium_month"  # "premium_month" or "premium_year"


class PaymentResponse(BaseModel):
    payment_url: str
    payment_id: str


class WebhookPayload(BaseModel):
    action: str
    type: str
    data: dict
    api_version: str
