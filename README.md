# ha-vizio-conjure

[![CI](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/ci.yml)
[![Prek](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/prek.yml/badge.svg?branch=main)](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/prek.yml)
[![Latest release](https://img.shields.io/github/v/release/joebeeson/ha-vizio-conjure?include_prereleases)](https://github.com/joebeeson/ha-vizio-conjure/releases)
[![License](https://img.shields.io/github/license/joebeeson/ha-vizio-conjure)](LICENSE)

Home Assistant integration for VIZIO Conjure.

## Current status

Milestone 2 now pairs a TV through Home Assistant, stores named targets, exposes
Conjure session state, and provides launch, Lovelace-view, reload, exit, and
allowlisted remote-key actions. A page receives a short-lived bridge capability
in the URL fragment; no long-lived Home Assistant token is sent to a generic
page.

## Planned boundary

Home Assistant launches and presents developer-hosted Conjure pages through the
Python library. TV pages must never receive a long-lived Home Assistant access
or refresh token. The integration uses a short-lived signed dashboard path and
a narrow capability bridge instead. The signed Lovelace path remains a physical
TV acceptance gate because the page must also establish its live Home Assistant
WebSocket connection.

Do not commit pairing tokens, private URLs, household data, or captured TV
responses.

## First integration slice

Add **VIZIO Conjure** from Settings → Devices & services. Enter the TV host
and port, then enter the PIN shown on the TV. The PIN is transient; the token
is kept in Home Assistant's config entry storage.

The service can then launch a page:

```yaml
action: vizio_conjure.launch
data:
  url: http://LAN_HOST:8765/
```

The page must be reachable from the TV. The current implementation uses the
same app 17 / namespace 4 launch mapping as `vizaio-conjure`; it uses a small
compatibility path until the private Python library is publishable as a
runtime dependency.

Use `vizio_conjure.page_command` for the fixed page subjects (`page.navigate`,
`page.reload`, `page.focus`, and `session.close`) while a session is active.
Its payload is bounded JSON and cannot call arbitrary Home Assistant services.

## Named targets

Open the VIZIO Conjure config-entry options and enter a JSON list such as:

```json
[
  {"name": "Smoke", "kind": "url", "url": "http://192.168.20.107:8765/"},
  {
    "name": "Downstairs",
    "kind": "lovelace",
    "dashboard_path": "lovelace-cast",
    "view_path": "downstairs"
  }
]
```

Launch a named URL with:

```yaml
action: vizio_conjure.launch
data:
  target: Smoke
```

Launch a dashboard view with:

```yaml
action: vizio_conjure.show_lovelace_view
data:
  dashboard_path: lovelace-cast
  view_path: downstairs
```

The web SDK normalizes the measured VIZIO DOM key events and can install an
opt-in focus adapter. Pages should expose ordinary focusable controls; the SDK
does not draw a separate cursor or execute arbitrary Home Assistant services.

## Development

Run `just check` from the repository root. CI exercises the scaffold against
Home Assistant's current Python runtime with pytest-cov and pytest-datadir,
then runs Ruff and Pyrefly checks. Public releases also run HACS and Hassfest
validation.

## Installation

Until the integration is accepted into the HACS default catalog, add
`joebeeson/ha-vizio-conjure` as a custom repository in HACS with category
**Integration**. Install the `VIZIO Conjure` release, restart Home Assistant,
and add it from Settings → Devices & services. Upgrades preserve the config
entry and its stored pairing token.

Tagged releases attach the deterministic `vizio_conjure.zip` artifact. The
integration is designed for a TV-reachable Home Assistant URL and keeps
credentials out of page URLs, events, logs, and sensor attributes.
