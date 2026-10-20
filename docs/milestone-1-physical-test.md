# Milestone 1 physical test

This runbook verifies the complete path from Home Assistant to a VIZIO Conjure
page. It assumes the smoke page is served from a host the TV can reach on the
LAN.

## Before starting

- Keep the TV powered on and idle at the home screen.
- Confirm the serving host's LAN address and port. Do not use `localhost` in
  the URL sent to the TV.
- Start the smoke server from `vizaio-conjure`, for example:

  ```text
  uv run vizaio-conjure serve examples/smoke --bind 0.0.0.0 --port 8765
  ```

- Install the `custom_components/vizio_conjure` directory into the Home
  Assistant configuration and restart Home Assistant. This private repository
  is not a HACS catalog entry yet.

## Pair and launch

1. In Home Assistant, open **Settings → Devices & services → Add
   integration → VIZIO Conjure**.
2. Enter the TV's current host and port, such as `192.0.2.10:7345`, and a
   descriptive profile name. The address is an example; use the current TV
   identity from the existing VIZIO integration or a fresh discovery result.
3. Read the one-time PIN shown on the TV and enter it in Home Assistant. The
   PIN is not stored; the resulting token stays in the config entry.
4. Open **Developer tools → Actions**, select `vizio_conjure.launch`, and
   submit:

   ```yaml
   action: vizio_conjure.launch
   data:
     url: http://LAN_REACHABLE_HOST:8765/
   ```

## Acceptance record

Record only sanitized results:

- [ ] The config flow completed and created one VIZIO Conjure device.
- [ ] The smoke marker rendered on the physical TV.
- [ ] The smoke page reported the expected browser/runtime metadata.
- [ ] Home or the TV's normal exit control returned to the prior TV surface.
- [ ] The current app and return behavior were checked without recording
      pairing tokens or full TV responses.

### Completed run: 2026-10-20

- [x] The config flow paired the TV and created one VIZIO Conjure device.
- [x] Home Assistant launched the smoke page through `vizio_conjure.launch`.
- [x] The physical TV rendered the `CONJURE OK` marker.
- [x] The page reported the VIZIO SmartCast Conjure runtime, firmware, and
      `M65Q6-L4` model metadata.
- [x] The page received four remote events (left/right keydown and keyup).
- [x] The supported `EXIT` remote command returned the TV to its normal home
      app before the successful retry.
- [x] No pairing PIN, auth token, or full TV response was recorded.

If the launch fails, first verify that the TV can route to the page host and
that the URL uses the host's LAN address. The integration deliberately does
not send Home Assistant credentials to the page.
