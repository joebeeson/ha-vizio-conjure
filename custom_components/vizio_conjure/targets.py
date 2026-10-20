"""Named Conjure target validation and storage helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class TargetRecord:
    """A user-facing named target without credentials."""

    name: str
    kind: str
    url: str | None = None
    dashboard_path: str | None = None
    view_path: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        kind = self.kind.strip().lower()
        if not name:
            raise ValueError("target name must not be empty")
        if kind not in {"url", "lovelace"}:
            raise ValueError("target kind must be url or lovelace")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "kind", kind)
        if kind == "url":
            if not self.url:
                raise ValueError("URL targets require url")
            parsed = urlsplit(self.url.strip())
            if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
                raise ValueError("target url must be an absolute http or https URL")
            if parsed.username is not None or parsed.password is not None:
                raise ValueError("target url must not contain embedded credentials")
            object.__setattr__(self, "url", self.url.strip())
        else:
            dashboard = (self.dashboard_path or "lovelace").strip().strip("/")
            view = (self.view_path or "").strip().strip("/")
            if not view:
                raise ValueError("Lovelace targets require view_path")
            object.__setattr__(self, "dashboard_path", dashboard or "lovelace")
            object.__setattr__(self, "view_path", view)


def parse_targets(value: object) -> tuple[TargetRecord, ...]:
    """Parse the config-entry target list from JSON or structured data."""

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as err:
            raise ValueError("targets must be valid JSON") from err
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("targets must be a JSON list")
    records: list[TargetRecord] = []
    names: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("each target must be an object")
        record = TargetRecord(
            name=str(item.get("name", "")),
            kind=str(item.get("kind", "url")),
            url=item.get("url") if isinstance(item.get("url"), str) else None,
            dashboard_path=(
                item.get("dashboard_path") if isinstance(item.get("dashboard_path"), str) else None
            ),
            view_path=(item.get("view_path") if isinstance(item.get("view_path"), str) else None),
        )
        key = record.name.casefold()
        if key in names:
            raise ValueError(f"duplicate target name: {record.name}")
        names.add(key)
        records.append(record)
    return tuple(records)


def targets_json(targets: tuple[TargetRecord, ...]) -> str:
    """Serialize targets for the options form."""

    return json.dumps(
        [
            {
                key: value
                for key, value in {
                    "name": target.name,
                    "kind": target.kind,
                    "url": target.url,
                    "dashboard_path": target.dashboard_path,
                    "view_path": target.view_path,
                }.items()
                if value is not None
            }
            for target in targets
        ],
        indent=2,
    )


def find_target(targets: tuple[TargetRecord, ...], name: str) -> TargetRecord:
    """Find a named target case-insensitively."""

    needle = name.strip().casefold()
    for target in targets:
        if target.name.casefold() == needle:
            return target
    raise ValueError(f"unknown Conjure target: {name}")
