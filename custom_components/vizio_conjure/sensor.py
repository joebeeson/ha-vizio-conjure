"""Conjure session status sensor."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ConjureCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the session sensor for a paired Conjure entry."""

    runtime = hass.data[DOMAIN]["entries"][entry.entry_id]
    coordinator: ConjureCoordinator = runtime.coordinator
    async_add_entities([ConjureSessionSensor(coordinator, entry)])


class ConjureSessionSensor(CoordinatorEntity[ConjureCoordinator], SensorEntity):
    """Expose the current Conjure lifecycle and sanitized metadata."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM  # pyrefly: ignore [bad-override-mutable-attribute]
    _attr_icon = "mdi:television-play"
    _attr_native_unit_of_measurement = None
    _attr_options = ["idle", "launching", "active", "stopped", "unavailable", "error"]

    def __init__(self, coordinator: ConjureCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = "Conjure session"
        self._attr_unique_id = f"{entry.entry_id}_conjure_session"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "VIZIO",
            "model": "Conjure",
        }

    @property
    def native_value(self) -> str:
        snapshot = self.coordinator.data
        return snapshot.state if snapshot is not None else "unavailable"

    @property
    def available(self) -> bool:
        snapshot = self.coordinator.data
        return snapshot is not None and snapshot.state != "unavailable"

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        snapshot = self.coordinator.data
        if snapshot is None:
            return {}
        return {
            key: value
            for key, value in {
                "session_id": snapshot.session_id,
                "target_name": snapshot.target_name,
                "url": snapshot.url,
                "current_app_id": snapshot.current_app_id,
                "current_namespace": snapshot.current_namespace,
                "current_message": snapshot.current_message,
                "runtime": snapshot.runtime,
                "model": snapshot.model,
                "firmware": snapshot.firmware,
                "last_seen": snapshot.last_seen,
                "last_error": snapshot.last_error,
            }.items()
            if value is not None
        }
