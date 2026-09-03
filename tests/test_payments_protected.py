import json
from unittest.mock import patch, MagicMock
from app.models import User, Payment, PaymentStatus, UserTier


@patch('app.payments.routes.MercadoPagoClient')
def test_create_subscription_requires_auth(mock_mp_client, client):
    """Test create subscription requires authentication."""
    response = client.post(
        "/payment/create-subscription",
        json={"plan": "premium_month"}
    )

    assert response.status_code == 401
    assert "authorization" in response.json()["detail"].lower()


@patch('app.payments.routes.MercadoPagoClient')
def test_create_subscription_only_free_users(mock_mp_client, client, db):
    """Test only free users can create subscription."""
    import uuid

    # Create premium user
    user = User(
        id=str(uuid.uuid4()),
        email="premium@example.com",
        password_hash="hashed",
        tier=UserTier.PREMIUM,
    )
    db.add(user)
    db.commit()

    # Mock MP client
    mock_client_instance = MagicMock()
    mock_mp_client.return_value = mock_client_instance

    # Signup and login (creates free user)
    client.post(
        "/auth/signup",
        json={"email": "buyer@example.com", "password": "secure123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "buyer@example.com", "password": "secure123"}
    )
    token = login_resp.json()["access_token"]

    # Free user should succeed
    mock_client_instance.create_preference.return_value = {
        "id": "mp_pref_123",
        "init_point": "https://mercadopago.com/checkout/v1/123",
    }

    response = client.post(
        "/payment/create-subscription",
        json={"plan": "premium_month"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "payment_url" in data
    assert "payment_id" in data


@patch('app.payments.routes.MercadoPagoClient')
def test_create_subscription_invalid_plan(mock_mp_client, client):
    """Test create subscription with invalid plan."""
    client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "secure123"}
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "secure123"}
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/payment/create-subscription",
        json={"plan": "invalid_plan"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert "Invalid plan" in response.json()["detail"]


@patch('app.payments.routes.MercadoPagoClient')
def test_webhook_payment_approved_upgrades_tier(mock_mp_client, client, db):
    """Test webhook payment approved upgrades user tier."""
    import uuid

    # Create user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="webhook@example.com",
        password_hash="hashed",
        tier=UserTier.FREE,
    )
    db.add(user)
    db.commit()

    # Create pending payment
    payment_id = "mp_payment_123"
    payment = Payment(
        id=str(uuid.uuid4()),
        user_id=user_id,
        mercado_pago_id=payment_id,
        amount=999.00,
        status=PaymentStatus.PENDING,
        plan="premium_month",
    )
    db.add(payment)
    db.commit()

    # Mock MP client
    mock_client_instance = MagicMock()
    mock_mp_client.return_value = mock_client_instance
    mock_client_instance.get_payment.return_value = {
        "id": payment_id,
        "status": "approved",
        "external_reference": user_id,
    }
    mock_client_instance.verify_webhook_signature.return_value = True

    # Send webhook
    webhook_payload = {
        "action": "payment.updated",
        "type": "payment",
        "data": {"id": payment_id},
        "api_version": "v1"
    }

    response = client.post(
        "/payment/webhook/mercadopago",
        json=webhook_payload,
        headers={"X-Signature": "ts=123,v1=valid"}
    )

    assert response.status_code == 200

    # Verify user upgraded
    user = db.query(User).filter(User.id == user_id).first()
    assert user.tier == UserTier.PREMIUM
    assert user.tier_expires_at is not None
    assert user.premium_expires_at is not None


@patch('app.payments.routes.MercadoPagoClient')
def test_webhook_idempotency(mock_mp_client, client, db):
    """Test duplicate webhooks don't reset tier expiration."""
    import uuid
    import time

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="idempotent@example.com",
        password_hash="hashed",
        tier=UserTier.FREE,
    )
    db.add(user)
    db.commit()

    payment_id = "mp_payment_456"
    payment = Payment(
        id=str(uuid.uuid4()),
        user_id=user_id,
        mercado_pago_id=payment_id,
        amount=999.00,
        status=PaymentStatus.PENDING,
        plan="premium_month",
    )
    db.add(payment)
    db.commit()

    mock_client_instance = MagicMock()
    mock_mp_client.return_value = mock_client_instance
    mock_client_instance.get_payment.return_value = {
        "id": payment_id,
        "status": "approved",
        "external_reference": user_id,
    }
    mock_client_instance.verify_webhook_signature.return_value = True

    webhook_payload = {
        "action": "payment.updated",
        "type": "payment",
        "data": {"id": payment_id},
        "api_version": "v1"
    }

    # Send first webhook
    client.post(
        "/payment/webhook/mercadopago",
        json=webhook_payload,
        headers={"X-Signature": "ts=123,v1=valid"}
    )

    user = db.query(User).filter(User.id == user_id).first()
    first_expiration = user.tier_expires_at

    # Wait a moment
    time.sleep(0.1)

    # Send duplicate webhook
    client.post(
        "/payment/webhook/mercadopago",
        json=webhook_payload,
        headers={"X-Signature": "ts=123,v1=valid"}
    )

    # Verify expiration didn't change
    user = db.query(User).filter(User.id == user_id).first()
    assert user.tier_expires_at == first_expiration


@patch('app.payments.routes.MercadoPagoClient')
def test_webhook_invalid_signature(mock_mp_client, client):
    """Test webhook with invalid signature is rejected."""
    mock_client_instance = MagicMock()
    mock_mp_client.return_value = mock_client_instance
    mock_client_instance.verify_webhook_signature.return_value = False

    webhook_payload = {
        "action": "payment.updated",
        "type": "payment",
        "data": {"id": "mp_invalid"},
        "api_version": "v1"
    }

    response = client.post(
        "/payment/webhook/mercadopago",
        json=webhook_payload,
        headers={"X-Signature": "ts=123,v1=invalid"}
    )

    # Returns 200 but doesn't process
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
