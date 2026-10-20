"""Short-lived receiver access tokens backed by a dedicated HA identity."""

from __future__ import annotations

from homeassistant.auth.const import GROUP_ID_ADMIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_RECEIVER_USER_ID


async def async_receiver_access_token(hass: HomeAssistant, entry: ConfigEntry) -> tuple[str, int]:
    """Return a short-lived access token for the Conjure receiver.

    The refresh token remains in Home Assistant's auth store. Only the derived
    access token is returned to the already-capability-authenticated receiver.
    """

    user_id = entry.data.get(CONF_RECEIVER_USER_ID)
    user = await hass.auth.async_get_user(user_id) if user_id else None
    if user is None:
        user = await hass.auth.async_create_system_user(
            f"VIZIO Conjure ({entry.title})",
            group_ids=[GROUP_ID_ADMIN],
            local_only=True,
        )
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_RECEIVER_USER_ID: user.id},
        )

    refresh_token = next(iter(user.refresh_tokens.values()), None)
    if refresh_token is None:
        refresh_token = await hass.auth.async_create_refresh_token(user)

    return (
        hass.auth.async_create_access_token(refresh_token),
        int(refresh_token.access_token_expiration.total_seconds()),
    )


async def async_remove_receiver_identity(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the dedicated system user when the config entry is deleted."""

    user_id = entry.data.get(CONF_RECEIVER_USER_ID)
    if user_id and (user := await hass.auth.async_get_user(user_id)) is not None:
        await hass.auth.async_remove_user(user)
