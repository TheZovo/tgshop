import requests
import time
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models.payment import Payment
from app.core.logger import logger

async def create_cryptomus_payment(amount: float, user_id: str):
    url = "https://api.cryptomus.com/v1/payment"
    headers = {
        "Authorization": settings.CRYPTOMUS_API_KEY,
        "Merchant": settings.CRYPTOMUS_MERCHANT_ID
    }
    data = {
        "amount": str(amount),
        "currency": "USD",
        "order_id": f"{user_id}_{int(time.time())}",
        "to_currency": "LTC"
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["result"]["url"], result["result"]["uuid"]
    except Exception as e:
        logger.error(f"Failed to create Cryptomus payment: {str(e)}")
        return None, None

async def check_cryptomus_payment(payment_uuid: str):
    url = f"https://api.cryptomus.com/v1/payment/{payment_uuid}"
    headers = {
        "Authorization": settings.CRYPTOMUS_API_KEY,
        "Merchant": settings.CRYPTOMUS_MERCHANT_ID
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        status = response.json()["result"]["status"]
        with SessionLocal() as db:
            payment = db.query(Payment).filter(Payment.cryptomus_uuid == payment_uuid).first()
            if payment:
                payment.status = status
                db.commit()
        return status
    except Exception as e:
        logger.error(f"Failed to check Cryptomus payment: {str(e)}")
        return None