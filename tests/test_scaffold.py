import asyncio
import importlib
import json
from pathlib import Path

from custom_components.vizio_conjure import async_setup


def test_manifest_declares_private_integration_domain() -> None:
    manifest = json.loads(
        Path("custom_components/vizio_conjure/manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["domain"] == "vizio_conjure"
    assert manifest["config_flow"] is True
    assert manifest["requirements"] == ["vizaio>=0.7,<0.8"]


def test_integration_package_imports() -> None:
    module = importlib.import_module("custom_components.vizio_conjure")
    assert module.__name__ == "custom_components.vizio_conjure"


def test_services_describe_launch_action() -> None:
    services = Path("custom_components/vizio_conjure/services.yaml").read_text(encoding="utf-8")
    assert "launch:" in services
    assert "LAN-reachable HTTP or HTTPS" in services


def test_setup_registers_milestone_two_actions() -> None:
    class Services:
        def __init__(self) -> None:
            self.names: list[str] = []

        def async_register(self, domain: str, name: str, handler, schema=None) -> None:
            self.names.append(f"{domain}.{name}")

    class Http:
        def register_view(self, view) -> None:
            return None

    class Config:
        internal_url = "http://homeassistant.local:8123"
        external_url = None

    class FakeHass:
        data: dict[str, object] = {}
        services = Services()
        http = Http()
        config = Config()

    hass = FakeHass()
    assert asyncio.run(async_setup(hass, {})) is True  # pyrefly: ignore [bad-argument-type]
    assert hass.services.names == [
        "vizio_conjure.launch",
        "vizio_conjure.show_lovelace_view",
        "vizio_conjure.reload",
        "vizio_conjure.exit",
        "vizio_conjure.send_key",
        "vizio_conjure.page_command",
    ]
