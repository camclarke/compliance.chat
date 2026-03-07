"""
Token-based usage tracking and tier management.

Tracks per-user daily token consumption against tier limits.
Backed by a local JSON file (swappable to Cosmos DB in production).
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Tier configuration: tier_name -> daily_token_limit (None = unlimited)
TIER_LIMITS: Dict[str, Optional[int]] = {
    "free": 10_000,
    "pro": 100_000,
    "max": 500_000,
    "elite": None,  # Unlimited
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
USAGE_FILE = os.path.join(DATA_DIR, "user_usage.json")


class UsageTracker:
    """
    Thread-safe, file-backed per-user token usage tracker.
    Each user is identified by their Entra ID `sub` claim.
    """

    def __init__(self, filepath: str = USAGE_FILE):
        self._filepath = filepath
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not os.path.exists(filepath):
            self._write({})

    # ── Public API ──────────────────────────────────────────────

    def ensure_user(self, sub: str, name: str = "", email: str = "") -> dict:
        """Create user record if it doesn't exist. Returns the user record."""
        with self._lock:
            data = self._read()
            if sub not in data:
                data[sub] = {
                    "email": email,
                    "name": name,
                    "tier": "free",
                    "payment_provider": None,
                    "payment_customer_id": None,
                    "tokens_used_today": 0,
                    "last_query_date": self._today(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                self._write(data)
            return data[sub]

    def check_budget(self, sub: str) -> Tuple[bool, int, str, Optional[int]]:
        """
        Pre-flight budget check.

        Returns:
            (allowed, remaining_tokens, tier, daily_limit)
            - allowed: True if user can still make queries
            - remaining_tokens: tokens left today (0 if exhausted, -1 if unlimited)
            - tier: user's current tier name
            - daily_limit: the tier's daily limit (None if unlimited)
        """
        with self._lock:
            data = self._read()
            user = data.get(sub)
            if not user:
                free_limit = TIER_LIMITS["free"]
                return True, free_limit or 0, "free", free_limit

            # Reset daily counter if date changed
            self._maybe_reset_daily(data, sub)
            user = data[sub]

            tier = user.get("tier", "free")
            limit = TIER_LIMITS.get(tier)
            used = user.get("tokens_used_today", 0)

            if limit is None:  # Unlimited tier
                return True, -1, tier, None

            remaining = max(0, limit - used)
            allowed = remaining > 0
            return allowed, remaining, tier, limit

    def record_usage(self, sub: str, tokens_consumed: int) -> int:
        """
        Record tokens consumed after a successful AI response.

        Returns the new remaining token count (-1 if unlimited).
        """
        with self._lock:
            data = self._read()
            if sub not in data:
                return 0

            self._maybe_reset_daily(data, sub)
            data[sub]["tokens_used_today"] += tokens_consumed
            data[sub]["last_query_date"] = self._today()
            self._write(data)

            tier = data[sub].get("tier", "free")
            limit = TIER_LIMITS.get(tier)
            if limit is None:
                return -1
            return max(0, limit - data[sub]["tokens_used_today"])

    def set_tier(
        self,
        sub: str,
        tier: str,
        provider: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> None:
        """Update a user's subscription tier (called by billing webhooks)."""
        with self._lock:
            data = self._read()
            if sub not in data:
                data[sub] = {
                    "email": "",
                    "name": "",
                    "tier": tier,
                    "payment_provider": provider,
                    "payment_customer_id": customer_id,
                    "tokens_used_today": 0,
                    "last_query_date": self._today(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                data[sub]["tier"] = tier
                if provider is not None:
                    data[sub]["payment_provider"] = provider
                if customer_id is not None:
                    data[sub]["payment_customer_id"] = customer_id
            self._write(data)

    def get_user(self, sub: str) -> Optional[dict]:
        """Get a user's record."""
        with self._lock:
            data = self._read()
            return data.get(sub)

    def find_user_by_email(self, email: str) -> Optional[Tuple[str, dict]]:
        """Find a user by email. Returns (sub, record) or None."""
        with self._lock:
            data = self._read()
            for sub, record in data.items():
                if record.get("email", "").lower() == email.lower():
                    return sub, record
            return None

    # ── Internal helpers ────────────────────────────────────────

    def _maybe_reset_daily(self, data: dict, sub: str) -> None:
        """Reset daily counter if the date has changed (mutates in place)."""
        today = self._today()
        if data[sub].get("last_query_date") != today:
            data[sub]["tokens_used_today"] = 0
            data[sub]["last_query_date"] = today
            self._write(data)

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _read(self) -> dict:
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write(self, data: dict) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Singleton instance
usage_tracker = UsageTracker()
