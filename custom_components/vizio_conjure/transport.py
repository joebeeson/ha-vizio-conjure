"""VIZIO transport used by the Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from vizaio import AppConfig, DeviceType, Vizio

try:
    from vizaio_conjure import ConjureClient as LibraryConjureClient
    from vizaio_conjure import ConjureTarget as LibraryConjureTarget
except ImportError:  # pragma: no cover - used until the private library is publishable
    LibraryConjureClient = None
    LibraryConjureTarget = None


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


class ConjureConnection:
    """Open a short-lived authenticated vizaio session for each launch."""

    def __init__(self, *, host: str, auth_token: str) -> None:
        self.host = host
        self._auth_token = auth_token

    async def async_launch_url(self, url: str) -> ConjureTarget:
        target = ConjureTarget(url)
        async with Vizio(
            host=self.host,
            device_type=DeviceType.TV,
            auth_token=self._auth_token,
        ) as device:
            if LibraryConjureClient is not None and LibraryConjureTarget is not None:
                library_target = LibraryConjureTarget(
                    target.url,
                    app_id=target.app_id,
                    name_space=target.name_space,
                )
                await LibraryConjureClient(device).launch_url(library_target)
            else:
                await device.launch_app_config(
                    AppConfig(
                        app_id=target.app_id,
                        name_space=target.name_space,
                        message=target.url,
                    )
                )
        return target
