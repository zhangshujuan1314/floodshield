"""Mock notification provider with in-memory delivery tracking
and realistic status transitions."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

TZ_SHANGHAI = timezone(timedelta(hours=8))

# In-memory store for deliveries
_deliveries: dict[str, dict[str, Any]] = {}


class MockNotificationProvider:
    async def dispatch(
        self,
        subscription_id: str,
        channel: str,
        recipient: str,
        message: str,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        # Idempotency: check if a delivery with the same key already exists
        if idempotency_key:
            for existing in _deliveries.values():
                if existing.get("idempotency_key") == idempotency_key:
                    return existing  # Return existing delivery, don't create duplicate

        now = datetime.now(TZ_SHANGHAI)
        delivery_id = str(uuid.uuid4())

        delivery = {
            "id": delivery_id,
            "idempotency_key": idempotency_key,
            "subscription_id": subscription_id,
            "channel": channel,
            "recipient": recipient,
            "message": message,
            "status": "pending",  # Start as pending, not sent
            "created_at": now.isoformat(),
            "sent_at": None,
            "delivered_at": None,
            "error_message": None,
            "retry_count": 0,
            "metadata": metadata or {},
        }

        # Simulate send with retry logic
        try:
            # Mock: simulate successful send
            delivery["status"] = "sent"
            delivery["sent_at"] = now.isoformat()
        except Exception as e:
            delivery["status"] = "failed"
            delivery["error_message"] = str(e)

        _deliveries[delivery_id] = delivery
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
        results = []
        for recipient in recipients:
            result = await self.dispatch(
                subscription_id=str(uuid.uuid4()),
                channel=channel,
                recipient=recipient,
                message=message,
                metadata=metadata,
            )
            results.append(result)
        return results

    def clear(self) -> None:
        _deliveries.clear()


provider = MockNotificationProvider()
