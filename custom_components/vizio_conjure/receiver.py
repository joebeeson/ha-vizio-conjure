"""Authenticated Home Assistant dashboard receiver page."""

from __future__ import annotations

import json

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .bridge import BridgeRegistry
from .identity import async_receiver_access_token

RECEIVER_HTML = r"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIZIO Conjure receiver</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#111;color:#eee;font:16px system-ui,sans-serif}
#dashboard{display:block;border:0;width:100%;height:100%;background:#111}
#status{position:fixed;inset:0;z-index:2;display:grid;place-items:center;background:#111;color:#eee}
#status[hidden]{display:none}
</style>
</head>
<body><div id="status">Connecting to Home Assistant…</div><iframe id="dashboard" title="Home Assistant dashboard" hidden></iframe>
<script>
(async () => {
  const params = new URLSearchParams(location.hash.slice(1));
  const capability = params.get("conjure_capability");
  const endpoint = params.get("conjure_endpoint");
  const target = params.get("conjure_target");
  const focusStyle = ["off", "outline", "glow"].includes(params.get("conjure_focus_style")) ? params.get("conjure_focus_style") : "outline";
  const status = document.getElementById("status");
  const frame = document.getElementById("dashboard");
  let focusDocument;
  let focusedElement;
  const publish = async (subject, payload) => {
    if (!endpoint || !capability) return;
    try { await fetch(endpoint, {method:"POST", headers:{"Content-Type":"text/plain"}, body:JSON.stringify({capability,subject,payload})}); } catch (_) {}
  };
  const labelFor = (element) => (element?.getAttribute("aria-label") || element?.textContent || element?.id || element?.tagName || "").trim().slice(0, 160);
  const focusable = (root) => {
    const result = [];
    const visit = (node) => {
      if (!node || !node.querySelectorAll) return;
      for (const element of node.querySelectorAll("*")) {
        if (element.nodeType !== 1) continue;
        const style = element.ownerDocument.defaultView?.getComputedStyle(element);
        const isFocusable = element.matches("a[href],button,input,select,textarea,[role=button],[tabindex]:not([tabindex='-1'])") || element.tabIndex >= 0;
        const disabled = element.hasAttribute("disabled") || element.getAttribute("aria-disabled") === "true";
        if (isFocusable && !disabled && style?.display !== "none" && style?.visibility !== "hidden" && element.getClientRects().length) result.push(element);
        if (element.shadowRoot) visit(element.shadowRoot);
      }
    };
    visit(root);
    return result;
  };
  const activeElement = (doc) => {
    let active = doc.activeElement;
    while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
    return active;
  };
  const installStyle = (root) => {
    if (focusStyle === "off") return;
    const owner = root.head || root;
    if (!owner || owner.querySelector?.("#vizio-conjure-focus-style")) return;
    const ownerDocument = root.ownerDocument || root;
    const style = ownerDocument.createElement("style");
    style.id = "vizio-conjure-focus-style";
    style.textContent = focusStyle === "glow"
      ? ".vizio-conjure-focused,:focus-visible{outline:4px solid #21d4fd!important;outline-offset:5px!important;box-shadow:0 0 0 7px rgba(33,212,253,.35),0 0 22px 8px rgba(33,212,253,.55)!important;border-radius:4px!important}"
      : ".vizio-conjure-focused,:focus-visible{outline:4px solid #21d4fd!important;outline-offset:4px!important;border-radius:4px!important}";
    owner.appendChild(style);
  };
  const installStyles = (doc) => {
    installStyle(doc);
    for (const element of doc.querySelectorAll("*")) if (element.shadowRoot) installStyle(element.shadowRoot);
  };
  const setFocus = (element, action = "focus") => {
    if (!element) return;
    focusedElement?.classList.remove("vizio-conjure-focused");
    focusedElement = element;
    element.classList.add("vizio-conjure-focused");
    element.focus({preventScroll:true});
    void publish("page.focus", {tag:element.tagName.toLowerCase(), label:labelFor(element), action});
  };
  const moveFocus = (key) => {
    const elements = focusable(focusDocument);
    if (!elements.length) return;
    const current = activeElement(focusDocument);
    if (!current || !elements.includes(current)) { setFocus(elements[0], "initial"); return; }
    const currentRect = current.getBoundingClientRect();
    const currentX = currentRect.left + currentRect.width / 2;
    const currentY = currentRect.top + currentRect.height / 2;
    const direction = {UP:[0,-1],DOWN:[0,1],LEFT:[-1,0],RIGHT:[1,0]}[key];
    if (!direction) return;
    const candidates = elements.filter((element) => element !== current).map((element) => {
      const rect = element.getBoundingClientRect();
      const x = rect.left + rect.width / 2, y = rect.top + rect.height / 2;
      const dx = x - currentX, dy = y - currentY;
      const primary = dx * direction[0] + dy * direction[1];
      const perpendicular = Math.abs(dx * direction[1] - dy * direction[0]);
      return {element, score: primary + perpendicular * 2};
    }).filter((candidate) => candidate.score > 0).sort((a,b) => a.score - b.score);
    setFocus(candidates[0]?.element);
  };
  const handleKey = (event) => {
    if (event.type !== "keydown") return;
    if (focusStyle === "off") return;
    const key = {ArrowUp:"UP",ArrowDown:"DOWN",ArrowLeft:"LEFT",ArrowRight:"RIGHT",Enter:"OK",Space:"OK",Escape:"BACK",BrowserBack:"BACK"}[event.key];
    if (!key) return;
    event.preventDefault();
    event.stopPropagation();
    if (key === "UP" || key === "DOWN" || key === "LEFT" || key === "RIGHT") moveFocus(key);
    if (key === "OK") {
      const current = activeElement(focusDocument);
      if (current?.nodeType === 1 && typeof current.click === "function") { current.click(); void publish("page.interaction", {action:"ok", tag:current.tagName.toLowerCase(), label:labelFor(current)}); }
    }
    if (key === "BACK") void publish("page.interaction", {action:"back"});
  };
  const installFocus = (doc) => {
    focusDocument = doc;
    installStyles(doc);
    doc.addEventListener("keydown", handleKey, true);
    doc.addEventListener("keyup", handleKey, true);
    doc.addEventListener("focusin", (event) => {
      if (event.target?.nodeType === 1) {
        focusedElement?.classList.remove("vizio-conjure-focused");
        focusedElement = event.target;
        focusedElement.classList.add("vizio-conjure-focused");
        void publish("page.focus", {tag:focusedElement.tagName.toLowerCase(), label:labelFor(focusedElement)});
      }
    }, true);
    const Observer = doc.defaultView?.MutationObserver || MutationObserver;
    new Observer(() => installStyles(doc)).observe(doc.documentElement, {subtree:true, childList:true});
    if (focusStyle !== "off") setTimeout(() => { if (!activeElement(doc) || activeElement(doc) === doc.body) moveFocus("DOWN"); }, 1200);
  };
  const commandLoop = async () => {
    if (!endpoint || !capability) return;
    try {
      const response = await fetch(`${endpoint}?capability=${encodeURIComponent(capability)}`);
      if (!response.ok) return;
      const commands = (await response.json()).commands || [];
      for (const command of commands) {
        if (command.subject === "page.reload") frame.contentWindow?.location.reload();
        if (command.subject === "page.navigate" && typeof command.payload?.path === "string" && command.payload.path.startsWith("/") && !command.payload.path.startsWith("//")) frame.src = command.payload.path;
        if (command.subject === "page.focus" && typeof command.payload?.selector === "string") { try { setFocus(focusDocument?.querySelector(command.payload.selector)); } catch (_) {} }
        if (command.subject === "session.close") { await publish("page.interaction", {action:"close"}); frame.hidden = true; status.hidden = false; status.textContent = "Session closed"; }
      }
    } catch (_) {}
    setTimeout(commandLoop, 1000);
  };
  try {
    if (!capability || !endpoint || !target || !target.startsWith("/") || target.startsWith("//")) throw new Error("invalid receiver capability");
    const response = await fetch(location.pathname, {method:"POST", headers:{"Content-Type":"text/plain"}, body:JSON.stringify({capability})});
    if (!response.ok) throw new Error("receiver authorization failed");
    const token = await response.json();
    const expires = Date.now() + (Number(token.expires_in) * 1000);
    localStorage.setItem("hassTokens", JSON.stringify({hassUrl:location.origin,clientId:null,expires,refresh_token:"",access_token:token.access_token,expires_in:Number(token.expires_in)}));
    history.replaceState(null, "", location.pathname);
    frame.addEventListener("load", async () => {
      frame.hidden = false;
      status.hidden = true;
      try { installFocus(frame.contentDocument); } catch (_) { await publish("page.error", {message:"dashboard frame is not accessible"}); }
      await publish("page.ready", {runtime:"home-assistant-lovelace", focusStyle});
    }, {once:true});
    frame.src = target;
    document.addEventListener("keydown", handleKey, true);
    document.addEventListener("keyup", handleKey, true);
    void commandLoop();
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
