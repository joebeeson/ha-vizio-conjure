# ha-vizio-conjure

[![CI](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/ci.yml)
[![Prek](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/prek.yml/badge.svg?branch=main)](https://github.com/joebeeson/ha-vizio-conjure/actions/workflows/prek.yml)
[![Latest release](https://img.shields.io/github/v/release/joebeeson/ha-vizio-conjure?include_prereleases)](https://github.com/joebeeson/ha-vizio-conjure/releases)
[![License](https://img.shields.io/github/license/joebeeson/ha-vizio-conjure)](LICENSE)

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

## Development

Run `just check` from the repository root. CI exercises the scaffold against
Home Assistant's current Python runtime with pytest-cov and pytest-datadir,
then runs Ruff and Pyrefly checks. HACS and Hassfest validation are deferred
until the repository is ready for public catalog review.

Tagged releases package the component directory, manifest, README, and license
as a private GitHub release artifact. Config flow, services, entities, HACS
catalog submission, and installation remain deferred until Milestone 2.
