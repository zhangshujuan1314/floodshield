"""Provider registry and factory for mock/swappable backends."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, dict[str, Any]] = {}


def register(category: str, name: str, provider: Any) -> None:
    _REGISTRY.setdefault(category, {})[name] = provider


def get(category: str, name: str) -> Any:
    cat = _REGISTRY.get(category)
    if cat is None or name not in cat:
        raise ValueError(f"Provider not found: {category}/{name}")
    return cat[name]


def factory(category: str, name: str) -> Any:
    """Import-and-register lazily, then return the provider instance."""
    import importlib

    module_map: dict[str, dict[str, str]] = {
        "weather": {
            "mock": "app.providers.mock_weather",
            "real": "app.providers.real_weather",
        },
        "map": {
            "mock": "app.providers.mock_map",
            "real": "app.providers.real_map",
        },
        "notification": {
            "mock": "app.providers.mock_notification",
            "real": "app.providers.real_notification",
        },
        "ai": {
            "noop": "app.providers.noop_ai",
            "real": "app.providers.real_ai",
        },
    }
    if category in module_map and name in module_map[category]:
        mod = importlib.import_module(module_map[category][name])
        instance = mod.provider  # each module exposes `provider`
        register(category, name, instance)
        return instance
    raise ValueError(f"Unknown provider: {category}/{name}")


def get_weather_provider() -> Any:
    """Return the configured weather provider.

    Falls back to mock if WEATHER_PROVIDER is 'real' but no API key is set.
    """
    from app.core.config import settings

    provider_name = settings.WEATHER_PROVIDER
    if provider_name == "real" and not settings.WEATHER_API_KEY:
        logger.warning(
            "WEATHER_PROVIDER is 'real' but WEATHER_API_KEY is empty; falling back to mock"
        )
        provider_name = "mock"

    return factory("weather", provider_name)
