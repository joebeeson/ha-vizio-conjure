import pytest

from custom_components.vizio_conjure.bridge import BridgeRegistry


class FakeBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def async_fire(self, event: str, data: dict[str, object]) -> None:
        self.events.append((event, data))


class FakeHass:
    def __init__(self) -> None:
        self.bus = FakeBus()


def test_bridge_publishes_allowlisted_events_and_commands() -> None:
    hass = FakeHass()
    registry = BridgeRegistry(hass, ttl_seconds=60)  # type: ignore[arg-type]
    session = registry.issue("session-1", entry_id="entry-1")

    registry.publish(session.capability, "page.ready", {"runtime": "vizio"})
    registry.queue_for_session(session.session_id, "page.reload", {})
    _, commands = registry.drain(session.capability)

    assert commands == [{"subject": "page.reload", "payload": {}}]
    assert hass.bus.events[0][1]["entry_id"] == "entry-1"


def test_bridge_rejects_unknown_or_expired_capabilities() -> None:
    registry = BridgeRegistry(FakeHass(), ttl_seconds=0)  # type: ignore[arg-type]
    session = registry.issue("session-1")
    with pytest.raises(ValueError):
        registry.publish(session.capability, "arbitrary.service", {})
    with pytest.raises(ValueError):
        registry.queue("missing", "page.reload", {})
