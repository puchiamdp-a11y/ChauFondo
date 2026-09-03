from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.utils import decode_token
from app.models import User

router = APIRouter(prefix="/payment", tags=["payment"])


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


@router.post("/create-subscription", status_code=201)
async def create_subscription(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Create premium subscription (authenticated users only).

    Returns: payment_url for Mercado Pago checkout
    """
    user = get_current_user_from_header(authorization, db)

    # Only free users can upgrade
    if user.tier != "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already premium or invalid tier",
        )

    # TODO: Implement Mercado Pago payment creation
    return {"payment_url": "https://mercadopago.com/placeholder"}


@router.post("/webhook/mercadopago", status_code=200)
async def handle_webhook(
    db: Session = Depends(get_db),
):
    """Handle Mercado Pago webhook notifications."""
    # TODO: Implement webhook handling
    return {"status": "ok"}
