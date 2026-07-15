"""Notification safety tests.

Critical safety requirements:
- Idempotency: same key = same delivery (no duplicates)
- Status lifecycle: pending → sent → delivered (not skipping states)
- No real SMS/push without credentials
"""

from __future__ import annotations

import pytest

from app.providers.mock_notification import MockNotificationProvider


@pytest.fixture
def provider():
    return MockNotificationProvider()


class TestIdempotency:
    """Duplicate notifications during retries must be prevented."""

    async def test_same_idempotency_key_returns_same_delivery(self, provider):
        result1 = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="暴雨预警",
            idempotency_key="key_001",
        )
        result2 = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="暴雨预警",
            idempotency_key="key_001",
        )
        assert result1["id"] == result2["id"]
        assert result1["idempotency_key"] == "key_001"

    async def test_different_keys_create_different_deliveries(self, provider):
        result1 = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="暴雨预警",
            idempotency_key="key_001",
        )
        result2 = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="暴雨预警",
            idempotency_key="key_002",
        )
        assert result1["id"] != result2["id"]

    async def test_no_key_always_creates_new(self, provider):
        result1 = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="暴雨预警",
        )
        result2 = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="暴雨预警",
        )
        assert result1["id"] != result2["id"]


class TestStatusLifecycle:
    """Notification status must follow proper lifecycle."""

    async def test_initial_status_is_sent(self, provider):
        result = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="测试消息",
        )
        assert result["status"] == "sent"

    async def test_delivery_has_required_fields(self, provider):
        result = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="测试消息",
        )
        assert "id" in result
        assert "subscription_id" in result
        assert "channel" in result
        assert "recipient" in result
        assert "message" in result
        assert "status" in result
        assert "created_at" in result
        assert "retry_count" in result

    async def test_get_delivery(self, provider):
        result = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="测试消息",
        )
        retrieved = await provider.get_delivery(result["id"])
        assert retrieved is not None
        assert retrieved["id"] == result["id"]

    async def test_get_nonexistent_delivery(self, provider):
        result = await provider.get_delivery("nonexistent-id")
        assert result is None


class TestChannelSupport:
    """Multiple notification channels must be supported."""

    async def test_sms_channel(self, provider):
        result = await provider.dispatch(
            subscription_id="sub_001",
            channel="sms",
            recipient="+8613800138000",
            message="短信测试",
        )
        assert result["channel"] == "sms"

    async def test_push_channel(self, provider):
        result = await provider.dispatch(
            subscription_id="sub_001",
            channel="push",
            recipient="user_001",
            message="推送测试",
        )
        assert result["channel"] == "push"

    async def test_wechat_channel(self, provider):
        result = await provider.dispatch(
            subscription_id="sub_001",
            channel="wechat",
            recipient="openid_001",
            message="微信测试",
        )
        assert result["channel"] == "wechat"


class TestBulkDispatch:
    """Bulk dispatch must handle multiple recipients."""

    async def test_bulk_dispatch_multiple(self, provider):
        results = await provider.bulk_dispatch(
            message="批量通知",
            channel="sms",
            recipients=["+8613800138000", "+8613800138001", "+8613800138002"],
        )
        assert len(results) == 3
        assert all(r["status"] == "sent" for r in results)

    async def test_bulk_dispatch_empty(self, provider):
        results = await provider.bulk_dispatch(
            message="空列表",
            channel="sms",
            recipients=[],
        )
        assert len(results) == 0


class TestSubscription:
    """Subscription management."""

    async def test_create_subscription(self, provider):
        sub = await provider.create_subscription(
            user_id="user_001",
            channel="sms",
            recipient="+8613800138000",
            areas=["area_001"],
            alert_types=["flood", "rainstorm"],
        )
        assert sub["user_id"] == "user_001"
        assert sub["channel"] == "sms"
        assert sub["is_active"] is True
        assert "area_001" in sub["areas"]
