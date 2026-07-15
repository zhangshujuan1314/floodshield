"""No-op AI provider returning template action cards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

TZ_SHANGHAI = timezone(timedelta(hours=8))


class NoopAIProvider:
    async def generate_action_cards(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        risk_level = context.get("risk_level", "medium")
        now = datetime.now(TZ_SHANGHAI)

        base_cards = [
            {
                "id": "card-001",
                "title": "Monitor water levels",
                "description": "Continue monitoring local water level gauges for changes.",
                "priority": "low",
                "category": "monitoring",
                "valid_until": (now + timedelta(hours=6)).isoformat(),
            },
            {
                "id": "card-002",
                "title": "Prepare emergency supplies",
                "description": "Ensure emergency supplies (water, food, flashlight, first aid kit) are ready.",
                "priority": "medium",
                "category": "preparation",
                "valid_until": (now + timedelta(hours=24)).isoformat(),
            },
        ]

        if risk_level in ("high", "extreme"):
            base_cards.append({
                "id": "card-003",
                "title": "Evacuate to nearest shelter",
                "description": "Risk level is high. Proceed to the nearest designated shelter immediately.",
                "priority": "critical",
                "category": "evacuation",
                "valid_until": (now + timedelta(hours=2)).isoformat(),
            })
            base_cards.append({
                "id": "card-004",
                "title": "Avoid flood-prone roads",
                "description": "Do not attempt to cross flooded roads. Use designated evacuation routes.",
                "priority": "high",
                "category": "safety",
                "valid_until": (now + timedelta(hours=4)).isoformat(),
            })

        return base_cards

    async def generate_voice_script(self, context: dict[str, Any]) -> str:
        risk_level = context.get("risk_level", "medium")
        area_name = context.get("area_name", "your area")
        language = context.get("language", "zh-CN")

        if language.startswith("zh"):
            if risk_level in ("high", "extreme"):
                return (
                    f"紧急通知：{area_name}当前洪水风险等级为{risk_level}。"
                    f"请立即撤离至最近的避难所。避免经过积水路段。"
                    f"如遇紧急情况请拨打119求助。"
                )
            return (
                f"安全提示：{area_name}当前洪水风险等级为{risk_level}。"
                f"请关注水位变化，做好防洪准备。"
            )

        if risk_level in ("high", "extreme"):
            return (
                f"URGENT NOTICE: Flood risk in {area_name} is {risk_level}. "
                f"Evacuate to the nearest shelter immediately. Avoid flooded roads. "
                f"Call emergency services if in danger."
            )
        return (
            f"Safety notice: Flood risk in {area_name} is {risk_level}. "
            f"Monitor water levels and prepare for possible evacuation."
        )


provider = NoopAIProvider()
