"""Core tap tests via the Singer SDK's built-in tap test framework.

All HTTP traffic is served by the `responses` mock registered in conftest.py;
no network access happens in CI.
"""

from __future__ import annotations

from singer_sdk.testing import get_tap_test_class

from tap_livetennisapi.tap import TapLiveTennisAPI

SAMPLE_CONFIG = {
    "api_key": "test-key-not-real",
    "start_date": "2026-08-01T00:00:00Z",
}

# Standard SDK test suite: CLI, discovery, catalog/schema validity, and a
# mocked sync of every stream with per-attribute type checks.
TestTapLiveTennisAPI = get_tap_test_class(
    tap_class=TapLiveTennisAPI,
    config=SAMPLE_CONFIG,
)
