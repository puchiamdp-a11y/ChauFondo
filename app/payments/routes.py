import json
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.utils import decode_token
from app.core.rate_limit_v2 import clear_client_cache
from app.models import User, Payment, PaymentStatus, UserTier
from app.payments.schemas import CreateSubscriptionRequest, PaymentResponse
from app.payments.utils import MercadoPagoClient, get_mercado_pago_amount, get_plan_duration_days
from app.core.config import settings

router = APIRouter(prefix="/payment", tags=["payment"])


def get_current_user_from_header(authorization: Optional[str], db: Session) -> User:
    """Extract user from Bearer token (REQUIRED)."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id: str = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user


@router.post("/create-subscription", response_model=PaymentResponse, status_code=201)
async def create_subscription(
    request: CreateSubscriptionRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Create premium subscription (PROTECTED - authenticated users only).

    Only free users can upgrade to premium.
    Returns: payment_url for Mercado Pago checkout
    """
    # Authenticate user (REQUIRED)
    user = get_current_user_from_header(authorization, db)

    # Only free tier users can upgrade
    if user.tier != UserTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be free tier to upgrade",
        )

    # Validate plan
    valid_plans = ["premium_month", "premium_year"]
    if request.plan not in valid_plans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}",
        )

    # Create Mercado Pago preference
    mp_client = MercadoPagoClient()
    try:
        amount = get_mercado_pago_amount(request.plan)
        mp_response = mp_client.create_preference(
            user_id=user.id,
            user_email=user.email,
            plan=request.plan,
            amount=amount,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}",
        )

    # Create payment record in database
    payment_id = str(uuid.uuid4())
    preference_id = mp_response.get("id")
    checkout_url = mp_response.get("init_point", "")

    payment = Payment(
        id=payment_id,
        user_id=user.id,
        mercado_pago_id=preference_id,
        amount=amount,
        status=PaymentStatus.PENDING,
        plan=request.plan,
    )
    db.add(payment)
    db.commit()

    return {
        "payment_id": payment_id,
        "payment_url": checkout_url,
    }


@router.post("/webhook/mercadopago", status_code=200)
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle Mercado Pago webhook notifications (PUBLIC).

    Verifies signature and processes payment status updates.
    """
    try:
        payload_str = await request.body()
        payload_str = payload_str.decode('utf-8')
        body = json.loads(payload_str)
    except Exception:
        return {"status": "ok"}

    # Verify webhook signature
    signature = request.headers.get("X-Signature", "")
    mp_client = MercadoPagoClient()
    if not mp_client.verify_webhook_signature(payload_str, signature):
        # Invalid signature - silently accept but don't process
        return {"status": "ok"}

    # Handle payment webhooks
    webhook_type = body.get("type")
    if webhook_type != "payment":
        return {"status": "ok"}

    payment_id = body.get("data", {}).get("id")
    if not payment_id:
        return {"status": "ok"}

    # Get payment status from Mercado Pago
    try:
        mp_payment = mp_client.get_payment(payment_id)
    except Exception:
        return {"status": "ok"}

    mp_status = mp_payment.get("status")
    external_reference = mp_payment.get("external_reference")

    if not external_reference:
        return {"status": "ok"}

    # Find user and payment in database
    user = db.query(User).filter(User.id == external_reference).first()
    if not user:
        return {"status": "ok"}

    payment = db.query(Payment).filter(
        Payment.mercado_pago_id == payment_id
    ).first()

    if not payment:
        return {"status": "ok"}

    # Update payment status based on Mercado Pago status
    if mp_status == "approved":
        # Only process if not already approved (idempotency)
        if payment.status != PaymentStatus.APPROVED:
            payment.status = PaymentStatus.APPROVED
            payment.paid_at = datetime.utcnow()

            # Upgrade user tier
            duration_days = get_plan_duration_days(payment.plan)
            user.tier = UserTier.PREMIUM
            user.tier_expires_at = datetime.utcnow() + timedelta(days=duration_days)
            user.premium_expires_at = datetime.utcnow() + timedelta(days=duration_days)

            # Clear rate limit cache for user (new limits apply)
            clear_client_cache(user.id)

            db.commit()

    elif mp_status == "rejected":
        if payment.status != PaymentStatus.REJECTED:
            payment.status = PaymentStatus.REJECTED
            db.commit()

    elif mp_status == "pending":
        if payment.status != PaymentStatus.PENDING:
            payment.status = PaymentStatus.PENDING
            db.commit()

    return {"status": "ok"}
