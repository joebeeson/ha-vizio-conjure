"""Helpers for building short-lived Home Assistant dashboard URLs."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urljoin

from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant


def lovelace_path(dashboard_path: str, view_path: str) -> str:
    """Return the canonical dashboard view path."""

    dashboard = dashboard_path.strip().strip("/") or "lovelace"
    view = view_path.strip().strip("/")
    if not view:
        raise ValueError("view_path must not be empty")
    if dashboard == "lovelace":
        return f"/lovelace/{view}"
    return f"/{dashboard}/{view}"


def build_signed_lovelace_url(
    hass: HomeAssistant,
    *,
    dashboard_path: str,
    view_path: str,
) -> str:
    """Build an expiring signed path using Home Assistant's content identity."""

    base = hass.config.internal_url or hass.config.external_url
    if not base:
        raise ValueError("Home Assistant internal_url or external_url is required")
    signed_path = async_sign_path(
        hass,
        lovelace_path(dashboard_path, view_path),
        timedelta(seconds=30),
        use_content_user=True,
    )
    return urljoin(f"{base.rstrip('/')}/", signed_path.lstrip("/"))
