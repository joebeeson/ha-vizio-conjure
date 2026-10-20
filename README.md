# ha-vizio-conjure

Private Home Assistant integration project for VIZIO Conjure.

## Current status

This repository is a scaffold while `vizaio-conjure` proves the supported
Conjure URL-launch path on real hardware. It intentionally does not install
services, entities, config flow, or HACS runtime behavior yet.

## Planned boundary

Home Assistant will eventually launch and present developer-hosted Conjure
pages through the Python library. TV pages must never receive a long-lived Home
Assistant access token. The integration will use short-lived URLs or a narrow
bridge protocol instead.

Do not commit pairing tokens, private URLs, household data, or captured TV
responses.
