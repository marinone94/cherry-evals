"""Polar.sh billing webhook endpoint."""

import base64
import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from cherry_evals.config import settings
from db.postgres.base import get_db
from db.postgres.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])


def _verify_polar_signature(payload: bytes, headers: dict[str, str]) -> bool:
    """Verify Polar webhook signature (Svix format).

    Polar uses Svix under the hood. Signature format:
    - Headers: webhook-id, webhook-timestamp, webhook-signature
    - Signed content: ``{msg_id}.{timestamp}.{body}``
    - Secret may have ``whsec_`` prefix (base64-encoded key)
    - Signature header: ``v1,<base64(HMAC-SHA256(key, signed_content))>``
    """
    if not settings.polar_webhook_secret:
        logger.warning("POLAR_WEBHOOK_SECRET not configured, rejecting webhook")
        return False

    msg_id = headers.get("webhook-id", "")
    timestamp = headers.get("webhook-timestamp", "")
    signature = headers.get("webhook-signature", "")

    if not all([msg_id, timestamp, signature]):
        return False

    # Svix secret format: whsec_<base64-key>
    secret = settings.polar_webhook_secret
    if secret.startswith("whsec_"):
        secret = secret[6:]

    try:
        key = base64.b64decode(secret)
    except Exception:
        key = secret.encode()

    to_sign = f"{msg_id}.{timestamp}.".encode() + payload
    expected = base64.b64encode(hmac.new(key, to_sign, hashlib.sha256).digest()).decode()

    # Signature header may contain multiple versions: "v1,<sig1> v1,<sig2>"
    for sig_part in signature.split():
        if sig_part.startswith("v1,"):
            if hmac.compare_digest(expected, sig_part[3:]):
                return True

    return False


@router.post("/webhooks/polar")
async def polar_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Polar.sh subscription lifecycle webhooks.

    Events handled:
    - subscription.created / subscription.updated → set tier to pro
    - subscription.canceled / subscription.revoked → set tier to free
    """
    body = await request.body()

    if not _verify_polar_signature(body, dict(request.headers)):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("type", "")
    data = event.get("data", {})

    # Extract customer email from the nested Polar event structure
    customer = data.get("customer", {})
    customer_email = customer.get("email", "")
    customer_id = str(customer.get("id", ""))

    if not customer_email:
        logger.warning("Polar webhook missing customer email: %s", event_type)
        return {"status": "ignored", "reason": "no customer email"}

    # Find user — prefer polar_customer_id for returning subscribers, fall back to email
    user = None
    if customer_id:
        user = db.execute(
            select(User).where(User.polar_customer_id == customer_id)
        ).scalar_one_or_none()
    if not user:
        user = db.execute(select(User).where(User.email == customer_email)).scalar_one_or_none()
    if not user:
        logger.warning("Polar webhook for unknown user: %s", customer_email)
        return {"status": "ignored", "reason": "user not found"}

    subscription_id = str(data.get("id", ""))
    subscription_status = data.get("status", "")

    if event_type in ("subscription.created", "subscription.updated"):
        # Determine tier from product ID
        product = data.get("product", {})
        product_id = str(product.get("id", "")) if isinstance(product, dict) else ""
        if not product_id:
            product_id = str(data.get("product_id", ""))

        if product_id and product_id == settings.polar_ultra_product_id:
            tier = "ultra"
        elif product_id and product_id == settings.polar_pro_product_id:
            tier = "pro"
        else:
            # Default to pro if product ID not configured yet
            tier = "pro"

        # Only upgrade tier when subscription is confirmed active
        if subscription_status in ("active", "trialing"):
            user.tier = tier
            # Trial is superseded by paid subscription
            user.trial_ends_at = None
            logger.info(
                "Upgraded user %s to %s (subscription %s)", user.email, tier, subscription_id
            )
        else:
            logger.info(
                "Subscription %s for %s has status %s — not upgrading tier yet",
                subscription_id,
                user.email,
                subscription_status,
            )

        user.polar_customer_id = customer_id
        user.polar_subscription_id = subscription_id
        user.subscription_status = subscription_status
    elif event_type in ("subscription.canceled", "subscription.revoked"):
        user.tier = "free"
        user.subscription_status = subscription_status
        logger.info("Downgraded user %s to free (subscription %s)", user.email, subscription_id)
    else:
        logger.info("Ignoring Polar event type: %s", event_type)
        return {"status": "ignored", "reason": f"unhandled event type: {event_type}"}

    db.commit()
    return {"status": "ok"}
