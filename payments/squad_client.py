import requests
from django.conf import settings


def squad_initiate_payment(*, email: str, amount_kobo: int, transaction_ref: str, customer_name: str | None = None):
    url = f"{settings.SQUAD_BASE_URL}/transaction/initiate"
    headers = {
        "Authorization": f"Bearer {settings.SQUAD_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "email": email,
        "amount": amount_kobo,                 # kobo
        "currency": getattr(settings, "SQUAD_CURRENCY", "NGN"),
        "initiate_type": "inline",             # required by docs
        "transaction_ref": transaction_ref,    # optional in docs, but use it for mapping
    }

    callback_url = getattr(settings, "SQUAD_CALLBACK_URL", None)
    if callback_url:
        payload["callback_url"] = callback_url

    if customer_name:
        payload["customer_name"] = customer_name

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    return resp.status_code, resp.json()


def squad_verify_transaction(transaction_ref: str):
    url = f"{settings.SQUAD_BASE_URL}/transaction/verify/{transaction_ref}"
    headers = {
        "Authorization": f"Bearer {settings.SQUAD_SECRET_KEY}",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    return resp.status_code, resp.json()
