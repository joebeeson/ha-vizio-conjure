# ha-vizio-conjure

[![CI](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/ci.yml)
[![Prek](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/prek.yml/badge.svg?branch=main)](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/prek.yml)
[![Latest release](https://img.shields.io/github/v/release/joebeeson/ha-vizio-conjure?include_prereleases)](https://github.com/joebeeson/ha-vizio-conjure/releases)
[![License](https://img.shields.io/github/license/joebeeson/ha-vizio-conjure)](LICENSE)

Private Home Assistant integration project for VIZIO Conjure.

## Current status

The first integration slice now pairs a TV through Home Assistant and exposes
the `vizio_conjure.launch` action for a LAN-reachable HTTP or HTTPS page. It is
still intentionally small: no Lovelace mirroring, page bridge, entities, or
HACS catalog submission yet.

## Planned boundary

Home Assistant launches and presents developer-hosted Conjure pages through the
Python library. TV pages must never receive a long-lived Home Assistant access
token. The integration will use short-lived URLs or a narrow bridge protocol
instead.

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

## Development

Run `just check` from the repository root. CI exercises the scaffold against
Home Assistant's current Python runtime with pytest-cov and pytest-datadir,
then runs Ruff and Pyrefly checks. HACS and Hassfest validation are deferred
until the repository is ready for public catalog review.

Tagged releases package the component directory, manifest, README, and license
as a private GitHub release artifact. Page bridging, entities, HACS catalog
submission, and installation guidance remain deferred until later milestones.
