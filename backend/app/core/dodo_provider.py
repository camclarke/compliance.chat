"""
Dodo Payments billing provider adapter.

Uses placeholder product IDs until the Dodo account is verified.
Once verified, set real product IDs in .env and switch environment to 'live_mode'.
"""

import logging
import os
from typing import Dict, Optional, Tuple

from app.core.billing_provider import BillingProvider

logger = logging.getLogger(__name__)

# Map tier names to Dodo product IDs (set in .env once account is verified)
TIER_PRODUCT_MAP: Dict[str, str] = {
    "pro": os.getenv("DODO_PRODUCT_PRO", "placeholder_pro_product_id"),
    "max": os.getenv("DODO_PRODUCT_MAX", "placeholder_max_product_id"),
    "elite": os.getenv("DODO_PRODUCT_ELITE", "placeholder_elite_product_id"),
}

# Reverse lookup: product_id -> tier
PRODUCT_TIER_MAP: Dict[str, str] = {v: k for k, v in TIER_PRODUCT_MAP.items()}


class DodoProvider(BillingProvider):
    """
    Dodo Payments adapter.

    In placeholder mode (no API key), returns a mock checkout URL.
    Once configured, creates real Dodo Checkout Sessions.
    """

    def __init__(self):
        self._api_key = os.getenv("DODO_PAYMENTS_API_KEY", "")
        self._webhook_secret = os.getenv("DODO_WEBHOOK_SECRET", "")
        self._environment = os.getenv("DODO_ENVIRONMENT", "test_mode")
        self._client = None

        if self._api_key and self._api_key != "placeholder":
            try:
                from dodopayments import AsyncDodoPayments
                self._client = AsyncDodoPayments(
                    bearer_token=self._api_key,
                    environment=self._environment,
                )
                logger.info("Dodo Payments client initialized in %s", self._environment)
            except ImportError:
                logger.warning("dodopayments package not installed. Running in placeholder mode.")
        else:
            logger.info("Dodo Payments running in PLACEHOLDER mode (no API key configured)")

    @property
    def provider_name(self) -> str:
        return "dodo"

    async def create_checkout(
        self,
        user_sub: str,
        user_email: str,
        tier: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        product_id = TIER_PRODUCT_MAP.get(tier)
        if not product_id:
            raise ValueError(f"Unknown tier: {tier}")

        # ── Placeholder mode ──────────────────────────────────
        if not self._client:
            logger.info(
                "PLACEHOLDER: Would create Dodo checkout for user=%s tier=%s product=%s",
                user_sub, tier, product_id,
            )
            # Return a placeholder URL that shows the pricing page instead
            return f"{cancel_url}?checkout=placeholder&tier={tier}"

        # ── Real Dodo API call ────────────────────────────────
        session = await self._client.checkout_sessions.create(
            product_cart=[{"product_id": product_id, "quantity": 1}],
            payment_link=True,
            customer={"email": user_email},
            metadata={"entra_sub": user_sub, "tier": tier},
            success_url=success_url,
            # Note: Dodo may not support cancel_url directly;
            # the user can close the tab to cancel.
        )

        checkout_url = getattr(session, "checkout_url", None) or getattr(session, "url", "")
        logger.info("Created Dodo checkout session: %s for tier %s", session.session_id, tier)
        return checkout_url

    async def handle_webhook(self, payload: bytes, headers: dict) -> Optional[Tuple[str, str]]:
        """
        Process Dodo webhook events.
        
        Expected events:
        - subscription.active: user's subscription is now active
        - subscription.cancelled: user cancelled
        """
        import json

        # ── Placeholder mode ──────────────────────────────────
        if not self._client:
            try:
                event = json.loads(payload)
                logger.info("PLACEHOLDER webhook received: %s", event)
                email = event.get("customer", {}).get("email", "")
                tier = event.get("metadata", {}).get("tier", "pro")
                if email:
                    return email, tier
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Failed to parse placeholder webhook: %s", e)
            return None

        # ── Real webhook processing ───────────────────────────
        # TODO: Verify webhook signature using self._webhook_secret
        try:
            event = json.loads(payload)
            event_type = event.get("type", "")

            if event_type in ("subscription.active", "subscription.created"):
                email = event.get("customer", {}).get("email", "")
                product_id = event.get("product_id", "")
                tier = PRODUCT_TIER_MAP.get(product_id, "pro")
                if email:
                    logger.info("Dodo subscription activated: %s -> %s", email, tier)
                    return email, tier

            elif event_type in ("subscription.cancelled", "subscription.deleted"):
                email = event.get("customer", {}).get("email", "")
                if email:
                    logger.info("Dodo subscription cancelled: %s -> free", email)
                    return email, "free"

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse Dodo webhook: %s", e)

        return None


# Singleton instance
dodo_provider = DodoProvider()
