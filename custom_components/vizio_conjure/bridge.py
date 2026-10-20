"""Short-lived page bridge capabilities and Home Assistant HTTP view."""

from __future__ import annotations

import json
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import BRIDGE_EVENT, BRIDGE_PATH, COMMAND_SUBJECTS, PAGE_SUBJECTS


@dataclass(slots=True)
class BridgeSession:
    """In-memory capability for one launched page."""

    session_id: str
    capability: str
    expires_at: float
    entry_id: str | None = None
    commands: deque[dict[str, Any]] = field(default_factory=deque)

    def expired(self) -> bool:
        return time.time() >= self.expires_at


class BridgeRegistry:
    """Issue and validate one-time, short-lived page capabilities."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        ttl_seconds: int = 300,
        endpoint: str | None = None,
    ) -> None:
        self.hass = hass
        self.ttl_seconds = ttl_seconds
        self.endpoint = endpoint or BRIDGE_PATH
        self._sessions: dict[str, BridgeSession] = {}

    def issue(self, session_id: str, *, entry_id: str | None = None) -> BridgeSession:
        capability = secrets.token_urlsafe(32)
        session = BridgeSession(
            session_id=session_id,
            capability=capability,
            expires_at=time.time() + self.ttl_seconds,
            entry_id=entry_id,
        )
        self._sessions[capability] = session
        return session

    def _get(self, capability: str) -> BridgeSession | None:
        session = self._sessions.get(capability)
        if session is None:
            return None
        if session.expired():
            self._sessions.pop(capability, None)
            return None
        return session

    def publish(self, capability: str, subject: str, payload: object) -> BridgeSession:
        session = self._get(capability)
        if session is None:
            raise ValueError("bridge capability is expired or invalid")
        if subject not in PAGE_SUBJECTS:
            raise ValueError("bridge subject is not allowed")
        if not isinstance(payload, dict):
            raise ValueError("bridge payload must be an object")
        if len(repr(payload)) > 16_384:
            raise ValueError("bridge payload is too large")
        self.hass.bus.async_fire(
            BRIDGE_EVENT,
            {
                "entry_id": session.entry_id,
                "session_id": session.session_id,
                "subject": subject,
                "payload": payload,
            },
        )
        return session

    def queue(self, capability: str, subject: str, payload: object) -> None:
        session = self._get(capability)
        if session is None:
            raise ValueError("bridge capability is expired or invalid")
        if subject not in COMMAND_SUBJECTS:
            raise ValueError("bridge command is not allowed")
        if not isinstance(payload, dict):
            raise ValueError("bridge payload must be an object")
        if len(repr(payload)) > 16_384:
            raise ValueError("bridge payload is too large")
        session.commands.append({"subject": subject, "payload": payload})

    def queue_for_session(self, session_id: str, subject: str, payload: object) -> None:
        """Queue a command for an active session without exposing its capability."""

        for session in self._sessions.values():
            if session.session_id == session_id:
                self.queue(session.capability, subject, payload)
                return
        raise ValueError("Conjure session is expired or invalid")

    def drain(self, capability: str) -> tuple[BridgeSession, list[dict[str, Any]]]:
        session = self._get(capability)
        if session is None:
            raise ValueError("bridge capability is expired or invalid")
        commands = list(session.commands)
        session.commands.clear()
        return session, commands


class BridgeView(HomeAssistantView):
    """Unauthenticated HTTP endpoint protected by a Conjure capability."""

    url = BRIDGE_PATH
    name = "api:vizio_conjure:bridge"
    requires_auth = False
    cors_allowed = True

    def __init__(self, registry: BridgeRegistry) -> None:
        self.registry = registry

    @staticmethod
    def _cors_headers(request: web.Request) -> dict[str, str]:
        origin = request.headers.get("Origin")
        return {"Access-Control-Allow-Origin": origin, "Vary": "Origin"} if origin else {}

    async def get(self, request: web.Request) -> web.Response:
        capability = request.query.get("capability", "")
        try:
            session, commands = self.registry.drain(capability)
        except ValueError as err:
            return self.json_message(str(err), status_code=401, headers=self._cors_headers(request))
        return self.json(
            {
                "session_id": session.session_id,
                "expires_at": session.expires_at,
                "commands": commands,
            },
            headers=self._cors_headers(request),
        )

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = json.loads(await request.text())
            capability = body["capability"]
            subject = body["subject"]
            payload = body.get("payload", {})
            if not isinstance(capability, str) or not isinstance(subject, str):
                raise ValueError("capability and subject must be strings")
            session = self.registry.publish(capability, subject, payload)
        except (KeyError, TypeError, ValueError, web.HTTPError) as err:
            return self.json_message(str(err), status_code=400, headers=self._cors_headers(request))
        return self.json(
            {"session_id": session.session_id, "accepted": True},
            headers=self._cors_headers(request),
        )
