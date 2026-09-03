import json
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import clear_user_cache
from app.models import User, Payment, PaymentStatus, UserTier, Image
from app.payments.schemas import (
    CreatePaymentRequest,
    PaymentResponse,
    PaymentStatusResponse,
    WebhookPayload,
)
from app.payments.utils import (
    MercadoPagoClient,
    get_mercado_pago_amount,
    get_plan_duration_days,
)
from app.auth.utils import decode_token
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["payments"])


def get_current_user_from_header(authorization: str, db: Session) -> User:
    """Extract user from Bearer token."""
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


@router.post("/create", response_model=PaymentResponse, status_code=201)
async def create_payment(
    request: CreatePaymentRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Create a payment preference in Mercado Pago.

    - **plan**: "premium_month" or "premium_year"

    Returns: payment_id, checkout_url, status, expires_at
    """
    # Authenticate user
    user = get_current_user_from_header(authorization, db)

    # Validate plan
    valid_plans = ["premium_month", "premium_year"]
    if request.plan not in valid_plans:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}",
        )

    # Get plan details
    amount = get_mercado_pago_amount(request.plan)

    # Create Mercado Pago preference
    mp_client = MercadoPagoClient()
    try:
        mp_response = mp_client.create_preference(
            user_id=user.id,
            user_email=user.email,
            plan=request.plan,
            amount=amount,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment preference: {str(e)}",
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
        "checkout_url": checkout_url,
        "status": "pending",
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
    }


@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
def get_payment_status(
    payment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Get payment status.

    Returns: payment_id, status, amount, plan, created_at, paid_at, tier_expires_at
    """
    # Authenticate user
    user = get_current_user_from_header(authorization, db)

    # Get payment
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return {
        "payment_id": payment.id,
        "status": payment.status.value,
        "amount": payment.amount,
        "plan": payment.plan,
        "created_at": payment.created_at.isoformat() + "Z",
        "paid_at": payment.paid_at.isoformat() + "Z" if payment.paid_at else None,
        "tier_expires_at": user.tier_expires_at.isoformat() + "Z" if user.tier_expires_at else None,
    }


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle Mercado Pago webhooks.

    Mercado Pago sends notifications about payment status changes.
    Verifies X-Signature header for authenticity.
    """
    try:
        payload_str = await request.body()
        payload_str = payload_str.decode('utf-8')
        body = json.loads(payload_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Verify webhook signature
    signature = request.headers.get("X-Signature", "")
    mp_client = MercadoPagoClient()
    if not mp_client.verify_webhook_signature(payload_str, signature):
        # Log suspicious activity but still acknowledge (don't reveal signature validation)
        return {"status": "ok"}

    # Handle different webhook types
    action = body.get("action")
    webhook_type = body.get("type")

    # We're interested in payment.updated events
    if webhook_type == "payment":
        payment_id = body.get("data", {}).get("id")

        if not payment_id:
            return {"status": "ok"}

        # Get payment from Mercado Pago API to verify status
        mp_client = MercadoPagoClient()
        try:
            mp_payment = mp_client.get_payment(payment_id)
        except Exception:
            # Even if we can't verify, acknowledge webhook
            return {"status": "ok"}

        mp_status = mp_payment.get("status")
        external_reference = mp_payment.get("external_reference")

        if not external_reference:
            return {"status": "ok"}

        # Find payment in our database using external_reference (user_id)
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
            # Only process if payment is transitioning to approved (idempotency)
            if payment.status != PaymentStatus.APPROVED:
                payment.status = PaymentStatus.APPROVED
                payment.paid_at = datetime.utcnow()

                # Upgrade user tier
                duration_days = get_plan_duration_days(payment.plan)
                user.tier = UserTier.PREMIUM
                user.tier_expires_at = datetime.utcnow() + timedelta(days=duration_days)

                # Clear rate limit cache for user
                clear_user_cache(user.id)

            db.commit()

        elif mp_status == "rejected":
            payment.status = PaymentStatus.REJECTED
            db.commit()

        elif mp_status == "pending":
            payment.status = PaymentStatus.PENDING
            db.commit()

    return {"status": "ok"}


@router.delete("/{payment_id}")
def cancel_payment(
    payment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Cancel a pending payment.

    Only pending payments can be cancelled.
    """
    # Authenticate user
    user = get_current_user_from_header(authorization, db)

    # Get payment
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel payment with status: {payment.status.value}",
        )

    payment.status = PaymentStatus.CANCELLED
    db.commit()

    return {"status": "cancelled"}
