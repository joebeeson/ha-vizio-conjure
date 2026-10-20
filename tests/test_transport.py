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
