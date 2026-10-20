from __future__ import annotations

import uuid

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from vizaio import DeviceType, Vizio, VizioError

from .const import (
    CONF_AUTH_TOKEN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_HOST,
    CONF_PROFILE_NAME,
    DEFAULT_DEVICE_NAME,
    DOMAIN,
)


class VizioConjureConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Pair a VIZIO TV and retain its token in a Home Assistant config entry."""

    VERSION = 1

    def __init__(self) -> None:
        self._vizio: Vizio | None = None
        self._pair_session = None
        self._host = ""
        self._profile_name = ""
        self._device_name = DEFAULT_DEVICE_NAME
        self._device_id = ""

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST].strip()
            self._profile_name = user_input[CONF_PROFILE_NAME].strip()
            self._device_name = user_input[CONF_DEVICE_NAME].strip() or DEFAULT_DEVICE_NAME
            if not self._host or any(character.isspace() for character in self._host):
                errors["base"] = "invalid_host"
            else:
                await self.async_set_unique_id(self._host.casefold())
                self._abort_if_unique_id_configured()
                self._device_id = f"ha-vizio-conjure:{uuid.uuid4()}"
                try:
                    await self._async_begin_pairing()
                except (OSError, VizioError):
                    errors["base"] = "cannot_connect"
        if self._pair_session is not None:
            return await self.async_step_pin()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(  # pyrefly: ignore [bad-argument-type]
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PROFILE_NAME, default="Living room TV"): str,
                    vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
                }
            ),
            errors=errors,
        )

    async def async_step_pin(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and self._pair_session is not None:
            try:
                token = await self._pair_session.complete(pin=user_input["pin"].strip())
            except (OSError, VizioError, ValueError):
                errors["base"] = "invalid_pin"
            else:
                await self._async_close_vizio()
                return self.async_create_entry(
                    title=self._profile_name or self._host,
                    data={
                        CONF_HOST: self._host,
                        CONF_DEVICE_ID: self._device_id,
                        CONF_DEVICE_NAME: self._device_name,
                        CONF_PROFILE_NAME: self._profile_name,
                        CONF_AUTH_TOKEN: token,
                    },
                )
        return self.async_show_form(
            step_id="pin",
            data_schema=vol.Schema({vol.Required("pin"): str}),  # pyrefly: ignore [bad-argument-type]
            errors=errors,
        )

    async def _async_begin_pairing(self) -> None:
        self._vizio = Vizio(host=self._host, device_type=DeviceType.TV)
        try:
            await self._vizio.__aenter__()
            self._pair_session = self._vizio.pair_session(
                device_id=self._device_id,
                device_name=self._device_name,
            )
            await self._pair_session.__aenter__()
        except BaseException:
            await self._async_close_vizio()
            raise

    async def _async_close_vizio(self) -> None:
        pair_session = self._pair_session
        vizio = self._vizio
        self._pair_session = None
        self._vizio = None
        try:
            if pair_session is not None:
                await pair_session.__aexit__(None, None, None)
        finally:
            if vizio is not None:
                await vizio.aclose()
