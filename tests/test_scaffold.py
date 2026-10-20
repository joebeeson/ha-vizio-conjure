import importlib
import json
from pathlib import Path


def test_manifest_declares_private_integration_domain() -> None:
    manifest = json.loads(
        Path("custom_components/vizio_conjure/manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["domain"] == "vizio_conjure"
    assert manifest["config_flow"] is False
    assert manifest["requirements"] == []


def test_integration_package_imports() -> None:
    module = importlib.import_module("custom_components.vizio_conjure")
    assert module.__name__ == "custom_components.vizio_conjure"
