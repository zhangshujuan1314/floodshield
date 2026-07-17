"""Real notification provider using configurable webhook/SMS APIs.

Supports SMS (Alibaba Cloud compatible), push, and email channels
via a configurable webhook endpoint or direct API calls.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TZ_SHANGHAI = timezone(timedelta(hours=8))

# In-memory delivery store (upgrade to DB later)
_deliveries: dict[str, dict[str, Any]] = {}

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 0.5  # seconds


class RealNotificationProvider:
    """Production notification provider with retry and delivery tracking."""

    async def dispatch(
        self,
        subscription_id: str,
        channel: str,
        recipient: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        # Idempotency: return existing delivery if key matches
        if idempotency_key:
            for existing in _deliveries.values():
                if existing.get("idempotency_key") == idempotency_key:
                    return existing

        now = datetime.now(TZ_SHANGHAI)
        delivery_id = str(uuid.uuid4())

        delivery = {
            "id": delivery_id,
            "idempotency_key": idempotency_key,
            "subscription_id": subscription_id,
            "channel": channel,
            "recipient": recipient,
            "message": message,
            "status": "pending",
            "created_at": now.isoformat(),
            "sent_at": None,
            "delivered_at": None,
            "error_message": None,
            "retry_count": 0,
            "metadata": metadata or {},
        }

        _deliveries[delivery_id] = delivery

        # Attempt send with exponential backoff retry
        for attempt in range(MAX_RETRIES):
            delivery["retry_count"] = attempt
            try:
                await self._send(channel, recipient, message)
                delivery["status"] = "sent"
                delivery["sent_at"] = datetime.now(TZ_SHANGHAI).isoformat()
                return delivery
            except Exception as e:
                logger.warning(
                    "Notification send attempt %d/%d failed for %s: %s",
                    attempt + 1, MAX_RETRIES, delivery_id, e,
                )
                delivery["error_message"] = str(e)
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(BASE_DELAY * (2 ** attempt))

        delivery["status"] = "failed"
        return delivery

    async def get_delivery(self, delivery_id: str) -> dict[str, Any] | None:
        return _deliveries.get(delivery_id)

    async def create_subscription(
        self,
        user_id: str,
        channel: str,
        recipient: str,
        areas: list[str] | None = None,
        alert_types: list[str] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(TZ_SHANGHAI)
        sub_id = str(uuid.uuid4())
        return {
            "id": sub_id,
            "user_id": user_id,
            "channel": channel,
            "recipient": recipient,
            "areas": areas or [],
            "alert_types": alert_types or ["flood", "rainfall"],
            "is_active": True,
            "created_at": now.isoformat(),
        }

    async def bulk_dispatch(
        self,
        message: str,
        channel: str,
        recipients: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        tasks = [
            self.dispatch(
                subscription_id=str(uuid.uuid4()),
                channel=channel,
                recipient=recipient,
                message=message,
                metadata=metadata,
            )
            for recipient in recipients
        ]
        return await asyncio.gather(*tasks)

    async def _send(self, channel: str, recipient: str, message: str) -> None:
        """Send a notification via the configured API endpoint.

        Raises an exception on failure so callers can retry.
        """
        if not settings.NOTIFICATION_API_URL:
            logger.info(
                "NOTIFICATION_API_URL not set; logging %s to %s: %s",
                channel, recipient, message[:80],
            )
            return

        payload: dict[str, Any] = {
            "channel": channel,
            "recipient": recipient,
            "message": message,
        }

        # Add channel-specific fields for Alibaba Cloud SMS compatibility
        if channel == "sms" and settings.SMS_API_KEY:
            payload["access_key"] = settings.SMS_API_KEY
            payload["access_secret"] = settings.SMS_API_SECRET

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(settings.NOTIFICATION_API_URL, json=payload)
            resp.raise_for_status()

    def clear(self) -> None:
        _deliveries.clear()


provider = RealNotificationProvider()
