"""VIZIO transport used by the Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit
from uuid import uuid4

from vizaio import AppConfig, DeviceType, Vizio, VizioError

try:
    from vizaio_conjure import ConjureClient as LibraryConjureClient
    from vizaio_conjure import ConjureTarget as LibraryConjureTarget
except ImportError:  # pragma: no cover - used until the private library is publishable
    LibraryConjureClient = None
    LibraryConjureTarget = None

from .const import ALLOWED_KEYS


@dataclass(frozen=True, slots=True)
class ConjureTarget:
    """Validated URL and the established Conjure launch constants."""

    url: str
    app_id: str = "17"
    name_space: int = 4

    def __post_init__(self) -> None:
        normalized = self.url.strip()
        parsed = urlsplit(normalized)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an absolute http or https URL")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("url must not contain embedded credentials")
        object.__setattr__(self, "url", normalized)


@dataclass(frozen=True, slots=True)
class ConjureSnapshot:
    """Sanitized state exposed by the Home Assistant sensor."""

    state: str = "idle"
    session_id: str | None = None
    target_name: str | None = None
    url: str | None = None
    current_app_id: str | None = None
    current_namespace: int | None = None
    current_message: str | None = None
    runtime: str | None = None
    model: str | None = None
    firmware: str | None = None
    last_seen: str | None = None
    last_error: str | None = None


def _with_bridge_fragment(
    url: str,
    *,
    capability: str,
    endpoint: str,
    target: str | None = None,
) -> str:
    """Attach bridge bootstrap data in the fragment, never the request URL."""

    parsed = urlsplit(url)
    fragment = parsed.fragment
    bridge = urlencode(
        {
            "conjure_capability": capability,
            "conjure_endpoint": endpoint,
            **({"conjure_target": target} if target is not None else {}),
        }
    )
    combined = f"{fragment}&{bridge}" if fragment else bridge
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, combined))


def _sanitize_message(message: object) -> str | None:
    """Keep app metadata useful without retaining URL credentials or tokens."""

    if message is None:
        return None
    value = str(message)
    parsed = urlsplit(value)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return value[:256]


class ConjureConnection:
    """Open a short-lived authenticated vizaio session for each launch."""

    def __init__(self, *, host: str, auth_token: str) -> None:
        self.host = host
        self._auth_token = auth_token
        self._snapshot = ConjureSnapshot()
        self._last_target: ConjureTarget | None = None

    @property
    def snapshot(self) -> ConjureSnapshot:
        """Return the latest in-memory snapshot."""

        return self._snapshot

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _with_device(self):
        return Vizio(
            host=self.host,
            device_type=DeviceType.TV,
            auth_token=self._auth_token,
        )

    async def async_launch_url(
        self,
        url: str,
        *,
        target_name: str | None = None,
        bridge: Any = None,
        entry_id: str | None = None,
        receiver_target: str | None = None,
    ) -> ConjureTarget:
        target = ConjureTarget(url)
        self._snapshot = ConjureSnapshot(
            state="launching",
            session_id=self._snapshot.session_id,
            target_name=target_name,
            url=target.url,
        )
        session = None
        launch_url = target.url
        if bridge is not None:
            session = bridge.issue(
                str(uuid4()),
                entry_id=entry_id,
                receiver=receiver_target is not None,
            )
            launch_url = _with_bridge_fragment(
                target.url,
                capability=session.capability,
                endpoint=getattr(bridge, "endpoint", "/api/vizio_conjure/bridge"),
                target=receiver_target,
            )
        launch_target = ConjureTarget(
            launch_url,
            app_id=target.app_id,
            name_space=target.name_space,
        )
        try:
            async with await self._with_device() as device:
                if LibraryConjureClient is not None and LibraryConjureTarget is not None:
                    library_target = LibraryConjureTarget(
                        launch_target.url,
                        app_id=launch_target.app_id,
                        name_space=launch_target.name_space,
                    )
                    await LibraryConjureClient(device).launch_url(library_target)
                else:
                    await device.launch_app_config(
                        AppConfig(
                            app_id=launch_target.app_id,
                            name_space=launch_target.name_space,
                            message=launch_target.url,
                        )
                    )
        except (OSError, VizioError, ValueError) as err:
            self._snapshot = ConjureSnapshot(
                state="error",
                session_id=session.session_id if session else None,
                target_name=target_name,
                url=target.url,
                last_error=str(err),
            )
            raise
        self._last_target = target
        self._snapshot = ConjureSnapshot(
            state="active",
            session_id=session.session_id if session else None,
            target_name=target_name,
            url=target.url,
            last_seen=self._now(),
        )
        return target

    async def async_send_key(self, key: str) -> None:
        """Send one safe remote key through the paired Conjure connection."""

        normalized = key.strip().upper()
        if normalized not in ALLOWED_KEYS:
            raise ValueError(f"unsupported Conjure key: {key}")
        async with await self._with_device() as device:
            await device.send_key(normalized)

    async def async_exit(self) -> None:
        """Return to SmartCast Home using the established EXIT command."""

        await self.async_send_key("EXIT")
        self._snapshot = ConjureSnapshot(
            state="stopped",
            session_id=self._snapshot.session_id,
            target_name=self._snapshot.target_name,
            url=self._snapshot.url,
            last_seen=self._now(),
        )

    async def async_reload(self, *, bridge: Any = None, entry_id: str | None = None) -> None:
        """Relaunch the active target with a fresh bridge capability."""

        if self._last_target is None:
            raise ValueError("no Conjure target is active")
        await self.async_launch_url(
            self._last_target.url,
            target_name=self._snapshot.target_name,
            bridge=bridge,
            entry_id=entry_id,
        )

    async def async_refresh(self) -> ConjureSnapshot:
        """Read current TV state and retain a sanitized snapshot."""

        try:
            async with await self._with_device() as device:
                current_app = None
                try:
                    extended = await device.get_state_extended()
                    current_app = extended.current_app
                    model = getattr(extended, "device_name", None)
                except (AttributeError, VizioError):
                    current_app = await device.get_current_app_config()
                    model = None
                if not model:
                    try:
                        model = (await device.get_device_info()).model
                    except (AttributeError, VizioError):
                        model = None
                firmware = self._snapshot.firmware
                if not firmware:
                    try:
                        firmware = await device.get_firmware_version()
                    except (AttributeError, VizioError):
                        firmware = None
                self._snapshot = ConjureSnapshot(
                    state=("active" if getattr(current_app, "app_id", None) == "17" else "stopped"),
                    session_id=self._snapshot.session_id,
                    target_name=self._snapshot.target_name,
                    url=self._snapshot.url,
                    current_app_id=getattr(current_app, "app_id", None),
                    current_namespace=getattr(current_app, "name_space", None),
                    current_message=_sanitize_message(getattr(current_app, "message", None)),
                    runtime=self._snapshot.runtime,
                    model=model,
                    firmware=firmware,
                    last_seen=self._now(),
                    last_error=None,
                )
        except (OSError, VizioError) as err:
            self._snapshot = ConjureSnapshot(
                state="unavailable",
                session_id=self._snapshot.session_id,
                target_name=self._snapshot.target_name,
                url=self._snapshot.url,
                last_error=str(err),
            )
        return self._snapshot
