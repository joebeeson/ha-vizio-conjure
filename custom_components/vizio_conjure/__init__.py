"""Home Assistant integration for VIZIO Conjure."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from vizaio import VizioError

from .const import (
    ATTR_ENTRY_ID,
    ATTR_URL,
    CONF_AUTH_TOKEN,
    CONF_HOST,
    DOMAIN,
    SERVICE_LAUNCH,
)
from .transport import ConjureConnection

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_URL): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register integration services."""

    hass.data.setdefault(DOMAIN, {})

    async def async_launch(call: ServiceCall) -> None:
        connections: dict[str, ConjureConnection] = hass.data[DOMAIN]
        entry_id = call.data.get(ATTR_ENTRY_ID)
        if entry_id:
            connection = connections.get(entry_id)
        elif len(connections) == 1:
            connection = next(iter(connections.values()))
        else:
            connection = None
        if connection is None:
            raise HomeAssistantError(
                "Specify entry_id when more than one VIZIO Conjure device is configured"
            )
        try:
            await connection.async_launch_url(call.data[ATTR_URL])
        except (OSError, ValueError, VizioError) as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_LAUNCH,
        async_launch,
        schema=SERVICE_SCHEMA,  # pyrefly: ignore [bad-argument-type]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one paired VIZIO device."""

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ConjureConnection(
        host=entry.data[CONF_HOST],
        auth_token=entry.data[CONF_AUTH_TOKEN],
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one paired VIZIO device."""

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
