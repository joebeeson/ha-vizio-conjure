# Milestone 2: dashboards and Conjure sessions

This milestone adds named targets, a session sensor, allowlisted remote-key
actions, and a short-lived page bridge.

## Named targets

Targets are stored in a config entry's options as JSON. They contain only a
display name and either an HTTP(S) URL or a Lovelace dashboard/view pair. URL
targets reject embedded credentials.

## Page bridge

When a page is launched, the integration adds a random capability to the URL
fragment. The fragment is not sent to the page server. The web SDK removes the
fragment from browser history and uses the capability to call the Home Assistant
bridge endpoint. Capabilities expire after five minutes and are kept in memory.

Accepted page subjects are:

- `page.ready`
- `page.error`
- `page.focus`
- `page.interaction`

The bridge does not execute arbitrary Home Assistant services. Home Assistant
actions remain the only way to control the TV or launch a new target.

## Lovelace view prototype

`vizio_conjure.show_lovelace_view` creates a 30-second Home Assistant signed
path and launches it through Conjure. The TV must be able to reach the
configured Home Assistant `internal_url` or `external_url`.

The signed path is a prototype gate. A physical test must verify both initial
Lovelace rendering and the frontend's live WebSocket connection. If the
frontend cannot authenticate its WebSocket from the signed path, the next
implementation slice must add an explicitly reviewed receiver identity rather
than placing a long-lived token in a page URL.

## Session sensor

Each paired entry exposes a diagnostic sensor with states `idle`, `launching`,
`active`, `stopped`, `unavailable`, and `error`. It polls the TV more often
while a Conjure app is active and retains only sanitized metadata.

## Physical acceptance

1. Configure a URL target and launch it.
2. Call `vizio_conjure.send_key` and verify page focus/activation.
3. Confirm the page emits `vizio_conjure_page_event` with a session ID.
4. Call `vizio_conjure.show_lovelace_view` for a dedicated dashboard view.
5. Verify the dashboard loads and receives live state updates.
6. Call `vizio_conjure.exit` and confirm return to SmartCast Home.
7. Check sanitized logs and browser history for absence of pairing or HA tokens.
