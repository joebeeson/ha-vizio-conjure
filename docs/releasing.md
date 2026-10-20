# Releasing

This repository is private while the VIZIO Conjure launch path is being
validated. Tagged releases create a reviewable GitHub release with a HACS
component archive; they do not install or publish an integration automatically.

1. Update the version in `custom_components/vizio_conjure/manifest.json` and
   `pyproject.toml`.
2. Run `just check` and review the generated coverage report.
3. Create and push an annotated `vX.Y.Z` tag.
4. The release workflow tests the scaffold, validates quality, packages the
   component, and attaches the zip to a GitHub release.

HACS catalog submission and validation, along with the config flow, services,
entities, and runtime integration, remain Milestone 2 work.
