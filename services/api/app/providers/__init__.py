"""Provider registry and factory for mock/swappable backends."""

from __future__ import annotations

from typing import Any

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
        },
        "map": {
            "mock": "app.providers.mock_map",
        },
        "notification": {
            "mock": "app.providers.mock_notification",
        },
        "ai": {
            "noop": "app.providers.noop_ai",
        },
    }
    if category in module_map and name in module_map[category]:
        mod = importlib.import_module(module_map[category][name])
        instance = mod.provider  # each module exposes `provider`
        register(category, name, instance)
        return instance
    raise ValueError(f"Unknown provider: {category}/{name}")
