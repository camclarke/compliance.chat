"""
Abstract billing provider interface.

Allows swapping payment processors (Dodo, Polar.sh, Paddle, Lemon Squeezy)
without changing the core billing logic.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class BillingProvider(ABC):
    """
    Abstract interface for payment provider integrations.
    Implement one adapter per provider (Dodo, Polar, Paddle, etc.).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique name for this provider (e.g., 'dodo', 'polar', 'paddle')."""
        ...

    @abstractmethod
    async def create_checkout(
        self,
        user_sub: str,
        user_email: str,
        tier: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """
        Create a hosted checkout session for a subscription.

        Args:
            user_sub: The Entra ID sub claim (unique user ID)
            user_email: User's email for the payment provider
            tier: Target tier name ('pro', 'max', 'elite')
            success_url: Redirect URL on successful payment
            cancel_url: Redirect URL on cancelled payment

        Returns:
            The checkout page URL to redirect the user to.
        """
        ...

    @abstractmethod
    async def handle_webhook(self, payload: bytes, headers: dict) -> Optional[Tuple[str, str]]:
        """
        Process an incoming webhook event from the provider.

        Args:
            payload: Raw request body bytes
            headers: Request headers (for signature verification)

        Returns:
            (user_email, new_tier) if the event updates a subscription,
            or None if the event should be ignored.
        """
        ...
