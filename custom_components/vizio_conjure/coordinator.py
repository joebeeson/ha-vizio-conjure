"""Polling coordinator for the Conjure session sensor."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .transport import ConjureConnection, ConjureSnapshot

_LOGGER = logging.getLogger(__name__)


class ConjureCoordinator(DataUpdateCoordinator[ConjureSnapshot]):
    """Poll the paired TV at a bounded rate."""

    def __init__(self, hass: HomeAssistant, connection: ConjureConnection) -> None:
        self.connection = connection
        super().__init__(
            hass,
            _LOGGER,
            name="VIZIO Conjure",
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> ConjureSnapshot:
        snapshot = await self.connection.async_refresh()
        self.update_interval = timedelta(
            seconds=15 if snapshot.state in {"launching", "active"} else 60
        )
        return snapshot
