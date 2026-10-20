"""Home Assistant integration for VIZIO Conjure."""

from __future__ import annotations

from dataclasses import dataclass

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from vizaio import VizioError

from .bridge import BridgeRegistry, BridgeView
from .const import (
    ALLOWED_KEYS,
    ATTR_DASHBOARD_PATH,
    ATTR_ENTRY_ID,
    ATTR_KEY,
    ATTR_TARGET,
    ATTR_TARGET_NAME,
    ATTR_URL,
    ATTR_VIEW_PATH,
    CONF_AUTH_TOKEN,
    CONF_HOST,
    CONF_TARGETS,
    DOMAIN,
    PLATFORMS,
    SERVICE_EXIT,
    SERVICE_LAUNCH,
    SERVICE_RELOAD,
    SERVICE_SEND_KEY,
    SERVICE_SHOW_LOVELACE_VIEW,
)
from .coordinator import ConjureCoordinator
from .lovelace import build_signed_lovelace_url
from .targets import TargetRecord, find_target, parse_targets
from .transport import ConjureConnection

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_URL): cv.string,
        vol.Optional(ATTR_TARGET): cv.string,
        vol.Optional(ATTR_TARGET_NAME): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)
SHOW_LOVELACE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_VIEW_PATH): cv.string,
        vol.Optional(ATTR_DASHBOARD_PATH, default="lovelace"): cv.string,
        vol.Optional(ATTR_TARGET_NAME): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)
RELOAD_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})
EXIT_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTRY_ID): cv.string})
SEND_KEY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_KEY): vol.In(sorted(ALLOWED_KEYS)),
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)


@dataclass(slots=True)
class EntryRuntime:
    """Runtime objects for one paired config entry."""

    connection: ConjureConnection
    coordinator: ConjureCoordinator


def _runtime_for_call(hass: HomeAssistant, call: ServiceCall) -> tuple[str, EntryRuntime]:
    entries: dict[str, EntryRuntime] = hass.data[DOMAIN]["entries"]
    entry_id = call.data.get(ATTR_ENTRY_ID)
    if entry_id:
        runtime = entries.get(entry_id)
    elif len(entries) == 1:
        entry_id, runtime = next(iter(entries.items()))
    else:
        runtime = None
    if runtime is None or entry_id is None:
        raise HomeAssistantError(
            "Specify entry_id when more than one VIZIO Conjure device is configured"
        )
    return entry_id, runtime


def _entry_targets(hass: HomeAssistant, entry_id: str) -> tuple[TargetRecord, ...]:
    entry = hass.config_entries.async_get_entry(entry_id)
    return parse_targets(entry.options.get(CONF_TARGETS, []) if entry else [])


def _resolve_url(hass: HomeAssistant, entry_id: str, call: ServiceCall) -> tuple[str, str | None]:
    raw_url = call.data.get(ATTR_URL)
    target_name = call.data.get(ATTR_TARGET) or call.data.get(ATTR_TARGET_NAME)
    if raw_url and target_name:
        raise HomeAssistantError("Use either url or target, not both")
    if raw_url:
        return raw_url, None
    if not target_name:
        raise HomeAssistantError("Specify url or target")
    try:
        target = find_target(_entry_targets(hass, entry_id), target_name)
    except ValueError as err:
        raise HomeAssistantError(str(err)) from err
    if target.kind != "url" or target.url is None:
        raise HomeAssistantError("The selected target is not a URL target")
    return target.url, target.name


def _resolve_lovelace_view(
    hass: HomeAssistant, entry_id: str, call: ServiceCall
) -> tuple[str, str, str | None]:
    target_name = call.data.get(ATTR_TARGET_NAME)
    if target_name:
        try:
            target = find_target(_entry_targets(hass, entry_id), target_name)
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err
        if target.kind != "lovelace":
            raise HomeAssistantError("The selected target is not a Lovelace target")
        return target.dashboard_path or "lovelace", target.view_path or "", target.name
    view_path = call.data.get(ATTR_VIEW_PATH)
    if not view_path:
        raise HomeAssistantError("Specify view_path or a named Lovelace target")
    return call.data.get(ATTR_DASHBOARD_PATH, "lovelace"), view_path, None


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register integration services and the capability bridge."""

    data = hass.data.setdefault(DOMAIN, {})
    data.setdefault("entries", {})
    base_url = hass.config.internal_url or hass.config.external_url
    endpoint = f"{base_url.rstrip('/')}/api/vizio_conjure/bridge" if base_url else None
    bridge = data.setdefault("bridge", BridgeRegistry(hass, endpoint=endpoint))
    if not data.get("bridge_view_registered"):
        hass.http.register_view(BridgeView(bridge))
        data["bridge_view_registered"] = True

    async def async_launch(call: ServiceCall) -> None:
        entry_id, runtime = _runtime_for_call(hass, call)
        url, target_name = _resolve_url(hass, entry_id, call)
        try:
            await runtime.connection.async_launch_url(
                url,
                target_name=target_name,
                bridge=bridge,
                entry_id=entry_id,
            )
            await runtime.coordinator.async_request_refresh()
        except (OSError, ValueError, VizioError) as err:
            raise HomeAssistantError(str(err)) from err

    async def async_show_lovelace(call: ServiceCall) -> None:
        entry_id, runtime = _runtime_for_call(hass, call)
        try:
            dashboard_path, view_path, target_name = _resolve_lovelace_view(hass, entry_id, call)
            url = build_signed_lovelace_url(
                hass,
                dashboard_path=dashboard_path,
                view_path=view_path,
            )
            await runtime.connection.async_launch_url(
                url,
                target_name=target_name,
                bridge=bridge,
                entry_id=entry_id,
            )
            await runtime.coordinator.async_request_refresh()
        except (OSError, ValueError, VizioError) as err:
            raise HomeAssistantError(str(err)) from err

    async def async_reload(call: ServiceCall) -> None:
        entry_id, runtime = _runtime_for_call(hass, call)
        try:
            await runtime.connection.async_reload(bridge=bridge, entry_id=entry_id)
            await runtime.coordinator.async_request_refresh()
        except (OSError, ValueError, VizioError) as err:
            raise HomeAssistantError(str(err)) from err

    async def async_exit(call: ServiceCall) -> None:
        _, runtime = _runtime_for_call(hass, call)
        try:
            await runtime.connection.async_exit()
            await runtime.coordinator.async_request_refresh()
        except (OSError, ValueError, VizioError) as err:
            raise HomeAssistantError(str(err)) from err

    async def async_send_key(call: ServiceCall) -> None:
        _, runtime = _runtime_for_call(hass, call)
        try:
            await runtime.connection.async_send_key(call.data[ATTR_KEY])
        except (OSError, ValueError, VizioError) as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(  # pyrefly: ignore [bad-argument-type]
        DOMAIN,
        SERVICE_LAUNCH,
        async_launch,
        schema=SERVICE_SCHEMA,  # pyrefly: ignore [bad-argument-type]
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SHOW_LOVELACE_VIEW,
        async_show_lovelace,
        schema=SHOW_LOVELACE_SCHEMA,  # pyrefly: ignore [bad-argument-type]
    )
    hass.services.async_register(  # pyrefly: ignore [bad-argument-type]
        DOMAIN,
        SERVICE_RELOAD,
        async_reload,
        schema=RELOAD_SCHEMA,  # pyrefly: ignore [bad-argument-type]
    )
    hass.services.async_register(  # pyrefly: ignore [bad-argument-type]
        DOMAIN,
        SERVICE_EXIT,
        async_exit,
        schema=EXIT_SCHEMA,  # pyrefly: ignore [bad-argument-type]
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_KEY,
        async_send_key,
        schema=SEND_KEY_SCHEMA,  # pyrefly: ignore [bad-argument-type]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one paired VIZIO device."""

    connection = ConjureConnection(
        host=entry.data[CONF_HOST],
        auth_token=entry.data[CONF_AUTH_TOKEN],
    )
    coordinator = ConjureCoordinator(hass, connection)
    hass.data[DOMAIN]["entries"][entry.entry_id] = EntryRuntime(connection, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one paired VIZIO device."""

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return unloaded
