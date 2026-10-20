import asyncio

import pytest
from vizaio import AppConfig

from custom_components.vizio_conjure import transport
from custom_components.vizio_conjure.transport import ConjureTarget


def test_target_uses_conjure_defaults() -> None:
    target = ConjureTarget(" http://example.test:8765/ ")

    assert target.url == "http://example.test:8765/"
    assert target.app_id == "17"
    assert target.name_space == 4


@pytest.mark.parametrize(
    "url",
    ["", "file:///tmp/page", "javascript:alert(1)", "http://user:pass@example.test/"],
)
def test_target_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(ValueError):
        ConjureTarget(url)


def test_sanitize_message_removes_url_credentials() -> None:
    message = transport._sanitize_message(
        "https://ha.local/lovelace/home?authSig=secret#capability=secret"
    )

    assert message == "https://ha.local/lovelace/home"


def test_bridge_fragment_keeps_capability_and_focus_style_in_fragment() -> None:
    launch = transport._with_bridge_fragment(
        "http://ha.local/api/vizio_conjure/receiver",
        capability="capability",
        endpoint="/api/vizio_conjure/bridge",
        target="/lovelace/home",
        focus_style="glow",
    )

    assert launch.startswith("http://ha.local/api/vizio_conjure/receiver#")
    assert "conjure_focus_style=glow" in launch
    assert "capability" in launch


def test_connection_maps_launch_to_upstream_app_config(monkeypatch) -> None:
    calls: list[AppConfig] = []

    class FakeDevice:
        async def launch_app_config(self, config: AppConfig) -> None:
            calls.append(config)

    class FakeVizio:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["host"] == "tv.local:7345"
            assert kwargs["auth_token"] == "AUTH:test"

        async def __aenter__(self) -> FakeDevice:
            return FakeDevice()

        async def __aexit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr(transport, "Vizio", FakeVizio)

    target = asyncio.run(
        transport.ConjureConnection(
            host="tv.local:7345",
            auth_token="AUTH:test",
        ).async_launch_url("http://server.local:8765/")
    )

    assert target == ConjureTarget("http://server.local:8765/")
    assert len(calls) == 1
    assert calls[0].app_id == "17"
    assert calls[0].name_space == 4
    assert calls[0].message == "http://server.local:8765/"


def test_connection_sends_only_allowlisted_keys(monkeypatch) -> None:
    keys: list[str] = []

    class FakeDevice:
        async def send_key(self, key: str) -> None:
            keys.append(key)

    class FakeVizio:
        def __init__(self, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> FakeDevice:
            return FakeDevice()

        async def __aexit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr(transport, "Vizio", FakeVizio)
    connection = transport.ConjureConnection(host="tv.local:7345", auth_token="AUTH:test")
    asyncio.run(connection.async_send_key("right"))
    assert keys == ["RIGHT"]

    with pytest.raises(ValueError):
        asyncio.run(connection.async_send_key("DROP_DATABASE"))


def test_connection_refreshes_current_app_and_marks_home_stopped(monkeypatch) -> None:
    class FakeApp:
        app_id = "1"
        name_space = 4
        message = '{"app":"home"}'

    class FakeState:
        current_app = FakeApp()
        device_name = "Living Room TV"

    class FakeDevice:
        async def launch_app_config(self, config: AppConfig) -> None:
            return None

        async def get_state_extended(self) -> FakeState:
            return FakeState()

        async def get_firmware_version(self) -> str:
            return "1.2.3"

    class FakeVizio:
        def __init__(self, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> FakeDevice:
            return FakeDevice()

        async def __aexit__(self, *exc: object) -> None:
            return None

    monkeypatch.setattr(transport, "Vizio", FakeVizio)
    connection = transport.ConjureConnection(host="tv.local:7345", auth_token="AUTH:test")
    asyncio.run(connection.async_launch_url("http://server.local:8765/"))
    snapshot = asyncio.run(connection.async_refresh())
    assert snapshot.state == "stopped"
    assert snapshot.current_app_id == "1"
    assert snapshot.model == "Living Room TV"
    assert snapshot.firmware == "1.2.3"
