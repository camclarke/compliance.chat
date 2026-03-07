"""
Billing API routes.

Handles checkout session creation and payment provider webhooks.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.auth import get_current_user
from app.core.usage import usage_tracker, TIER_LIMITS
from app.core.dodo_provider import dodo_provider
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/checkout")
async def create_checkout(
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Create a checkout session for the user to subscribe to a paid tier.
    Frontend redirects the user to the returned URL.
    """
    body = await request.json()
    tier = body.get("tier", "pro")

    if tier not in TIER_LIMITS or tier == "free":
        raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}. Choose pro, max, or elite.")

    user_sub = user.get("sub", "")
    user_email = user.get("email", "unknown@example.com")

    # Determine redirect URLs
    origin = request.headers.get("origin", "http://localhost:5173")
    success_url = f"{origin}?subscription=success&tier={tier}"
    cancel_url = f"{origin}?subscription=cancelled"

    try:
        checkout_url = await dodo_provider.create_checkout(
            user_sub=user_sub,
            user_email=user_email,
            tier=tier,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"checkout_url": checkout_url, "tier": tier}
    except Exception as e:
        logger.error("Failed to create checkout session: %s", e)
        raise HTTPException(status_code=500, detail=f"Billing error: {str(e)}")


@router.post("/webhook/dodo")
async def dodo_webhook(request: Request):
    """
    Webhook endpoint for Dodo Payments.
    Dodo sends events when subscriptions are created, updated, or cancelled.
    """
    payload = await request.body()
    headers = dict(request.headers)

    result = await dodo_provider.handle_webhook(payload, headers)

    if result:
        email, new_tier = result
        # Find user by email and update their tier
        user_record = usage_tracker.find_user_by_email(email)
        if user_record:
            sub, _ = user_record
            usage_tracker.set_tier(sub, new_tier, provider="dodo")
            logger.info("Updated user %s to tier %s via Dodo webhook", sub, new_tier)
        else:
            logger.warning("Webhook received for unknown email: %s", email)

    return {"status": "ok"}


@router.get("/tiers")
async def get_tiers():
    """Return available subscription tiers and their limits."""
    return {
        "tiers": [
            {
                "name": "free",
                "display_name": "Free",
                "price": "$0",
                "price_period": "",
                "daily_tokens": TIER_LIMITS["free"],
                "features": [
                    "10,000 tokens/day",
                    "Basic compliance queries",
                    "Community support",
                ],
            },
            {
                "name": "pro",
                "display_name": "Pro",
                "price": "$29",
                "price_period": "/mo",
                "daily_tokens": TIER_LIMITS["pro"],
                "features": [
                    "100,000 tokens/day",
                    "PDF document analysis",
                    "Priority support",
                    "Query history",
                ],
            },
            {
                "name": "max",
                "display_name": "Max",
                "price": "$99",
                "price_period": "/mo",
                "daily_tokens": TIER_LIMITS["max"],
                "features": [
                    "500,000 tokens/day",
                    "Unlimited PDF analysis",
                    "Dedicated support",
                    "API access",
                    "Team sharing",
                ],
            },
            {
                "name": "elite",
                "display_name": "Elite",
                "price": "$299",
                "price_period": "/mo",
                "daily_tokens": None,
                "features": [
                    "Unlimited tokens",
                    "Custom compliance rules",
                    "SLA guarantee",
                    "Dedicated account manager",
                    "Custom integrations",
                ],
            },
        ]
    }


@router.get("/usage")
async def get_usage(user: dict = Depends(get_current_user)):
    """Return the current user's usage stats and tier info."""
    user_sub = user.get("sub", "")
    user_record = usage_tracker.get_user(user_sub)

    if not user_record:
        return {
            "tier": "free",
            "tokens_used_today": 0,
            "daily_limit": TIER_LIMITS["free"],
            "remaining": TIER_LIMITS["free"],
        }

    tier = user_record.get("tier", "free")
    limit = TIER_LIMITS.get(tier)
    used = user_record.get("tokens_used_today", 0)

    return {
        "tier": tier,
        "tokens_used_today": used,
        "daily_limit": limit,
        "remaining": max(0, limit - used) if limit else None,
    }
