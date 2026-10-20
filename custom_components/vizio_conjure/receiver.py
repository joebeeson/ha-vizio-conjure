"""Authenticated Home Assistant dashboard receiver page."""

from __future__ import annotations

import json

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .bridge import BridgeRegistry
from .identity import async_receiver_access_token

RECEIVER_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIZIO Conjure receiver</title>
<style>html,body{margin:0;width:100%;height:100%;background:#111;color:#eee;font:16px system-ui,sans-serif}#status{display:grid;place-items:center;height:100%}</style>
</head>
<body><div id="status">Connecting to Home Assistant…</div>
<script>
(async () => {
  const params = new URLSearchParams(location.hash.slice(1));
  const capability = params.get("conjure_capability");
  const endpoint = params.get("conjure_endpoint");
  const target = params.get("conjure_target");
  const status = document.getElementById("status");
  const publish = async (subject, payload) => {
    if (!endpoint || !capability) return;
    try {
      await fetch(endpoint, {method:"POST", headers:{"Content-Type":"text/plain"}, body:JSON.stringify({capability,subject,payload})});
    } catch (_) {}
  };
  try {
    if (!capability || !endpoint || !target || !target.startsWith("/") || target.startsWith("//")) throw new Error("invalid receiver capability");
    const response = await fetch(location.pathname, {method:"POST", headers:{"Content-Type":"text/plain"}, body:JSON.stringify({capability})});
    if (!response.ok) throw new Error("receiver authorization failed");
    const token = await response.json();
    const expires = Date.now() + (Number(token.expires_in) * 1000);
    localStorage.setItem("hassTokens", JSON.stringify({hassUrl:location.origin,clientId:null,expires,refresh_token:"",access_token:token.access_token,expires_in:Number(token.expires_in)}));
    await publish("page.ready", {runtime:"home-assistant-lovelace"});
    history.replaceState(null, "", location.pathname);
    location.replace(target);
  } catch (error) {
    status.textContent = error instanceof Error ? error.message : "receiver error";
    await publish("page.error", {message:status.textContent});
  }
})();
</script></body></html>"""


class ReceiverView(HomeAssistantView):
    """Serve the receiver shell and exchange a capability for access."""

    url = "/api/vizio_conjure/receiver"
    name = "api:vizio_conjure:receiver"
    requires_auth = False

    def __init__(self, hass: HomeAssistant, registry: BridgeRegistry) -> None:
        self.hass = hass
        self.registry = registry

    async def get(self, request: web.Request) -> web.Response:
        return web.Response(
            text=RECEIVER_HTML,
            content_type="text/html",
            headers={"Cache-Control": "no-store"},
        )

    async def post(self, request: web.Request) -> web.Response:
        try:
            body = json.loads(await request.text())
            capability = body["capability"]
            if not isinstance(capability, str):
                raise ValueError("capability must be a string")
            session = self.registry.receiver_session(capability)
            if session.entry_id is None:
                raise ValueError("receiver session has no config entry")
            entry = self.hass.config_entries.async_get_entry(session.entry_id)
            if entry is None:
                raise ValueError("receiver config entry is unavailable")
            access_token, expires_in = await async_receiver_access_token(self.hass, entry)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as err:
            return self.json_message(str(err), status_code=401)
        return self.json(
            {"access_token": access_token, "expires_in": expires_in},
            headers={"Cache-Control": "no-store"},
        )
