# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-08-16

### Added

- Initial release, built with the Meltano Singer SDK.
- `players` stream (`GET /players`, FREE tier, FULL_TABLE, optional
  `player_search` setting).
- `fixtures` stream (`GET /fixtures`, FREE tier, FULL_TABLE — the endpoint
  exposes only the upcoming schedule and offers no date cursor).
- `live_matches` stream (`GET /matches?status=live`, FREE tier, FULL_TABLE
  snapshot).
- `match_history` stream (`GET /history/matches`, requires a BASIC+ key or
  any Historical Data API plan; INCREMENTAL on `scheduled_time` via the
  endpoint's `from` play-date filter).
- Bearer authentication from the `api_key` setting; optional `tour` filter;
  actionable error on the API's `403 upgrade_required`.
- Test suite on the SDK's built-in tap test framework with fully mocked
  responses (no network in CI).

[Unreleased]: https://github.com/livetennisapi/tap-livetennisapi/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/livetennisapi/tap-livetennisapi/releases/tag/v0.1.0
