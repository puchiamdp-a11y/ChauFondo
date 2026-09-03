import requests
import json
import hmac
import hashlib
from app.core.config import settings


class MercadoPagoClient:
    """Mercado Pago API client wrapper."""

    BASE_URL = "https://api.mercadopago.com"

    def __init__(self):
        self.token = settings.MERCADO_PAGO_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def create_preference(
        self,
        user_id: str,
        user_email: str,
        plan: str,
        amount: float,
        currency: str = "ARS",
    ) -> dict:
        """Create a payment preference in Mercado Pago."""
        plan_config = {
            "premium_month": {
                "title": "ChauFondo Premium - 1 Mes",
                "description": "100 descargas/mes + soporte prioritario",
                "duration": 30,
            },
            "premium_year": {
                "title": "ChauFondo Premium - 1 Año",
                "description": "100 descargas/mes + soporte prioritario + descuento",
                "duration": 365,
            },
        }

        config = plan_config.get(plan, plan_config["premium_month"])

        payload = {
            "items": [
                {
                    "title": config["title"],
                    "description": config["description"],
                    "quantity": 1,
                    "currency_id": currency,
                    "unit_price": amount,
                }
            ],
            "payer": {
                "email": user_email,
            },
            "external_reference": user_id,
            "notification_url": f"{settings.API_BASE_URL}/payment/webhook/mercadopago",
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/premium/success",
                "failure": f"{settings.FRONTEND_URL}/premium/failure",
                "pending": f"{settings.FRONTEND_URL}/premium/pending",
            },
            "auto_return": "approved",
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/checkout/preferences",
                json=payload,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Mercado Pago API error: {str(e)}")

    def get_payment(self, payment_id: str) -> dict:
        """Get payment details from Mercado Pago."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/v1/payments/{payment_id}",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Mercado Pago API error: {str(e)}")

    def verify_webhook_signature(self, payload_str: str, signature: str) -> bool:
        """Verify Mercado Pago webhook signature (X-Signature header)."""
        if not signature or not settings.MERCADO_PAGO_SECRET:
            return False

        try:
            parts = signature.split(',')
            timestamp = None
            received_signature = None

            for part in parts:
                if part.startswith('ts='):
                    timestamp = part.replace('ts=', '')
                elif part.startswith('v1='):
                    received_signature = part.replace('v1=', '')

            if not timestamp or not received_signature:
                return False

            message = f"{timestamp}.{payload_str}"
            calculated_signature = hmac.new(
                settings.MERCADO_PAGO_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(calculated_signature, received_signature)
        except Exception:
            return False


def get_mercado_pago_amount(plan: str) -> float:
    """Get amount for plan in ARS."""
    amounts = {
        "premium_month": 999.00,
        "premium_year": 9999.00,
    }
    return amounts.get(plan, 999.00)


def get_plan_duration_days(plan: str) -> int:
    """Get duration in days for plan."""
    durations = {
        "premium_month": 30,
        "premium_year": 365,
    }
    return durations.get(plan, 30)
