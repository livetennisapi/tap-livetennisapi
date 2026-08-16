"""Behavioural tests: auth header, params, incremental filter, tier errors."""

from __future__ import annotations

import pytest
import responses
from singer_sdk.exceptions import FatalAPIError

from tap_livetennisapi.tap import TapLiveTennisAPI

CONFIG = {
    "api_key": "test-key-not-real",
    "start_date": "2026-08-01T00:00:00Z",
}


def _get_stream(name: str, config: dict):
    tap = TapLiveTennisAPI(config=config, validate_config=True)
    return tap.streams[name]


def test_bearer_auth_header(mocked_api):
    """Requests carry Authorization: Bearer <api_key>."""
    stream = _get_stream("players", CONFIG)
    records = list(stream.get_records(context=None))
    assert records
    call = next(c for c in mocked_api.calls if "/players" in c.request.url)
    assert call.request.headers["Authorization"] == "Bearer test-key-not-real"


def test_live_matches_pins_status_live(mocked_api):
    """live_matches always queries /matches?status=live."""
    stream = _get_stream("live_matches", CONFIG)
    records = list(stream.get_records(context=None))
    assert records and records[0]["status"] == "live"
    call = next(
        c
        for c in mocked_api.calls
        if "/matches?" in c.request.url and "/history" not in c.request.url
    )
    assert "status=live" in call.request.url


def test_match_history_uses_start_date_as_from(mocked_api):
    """match_history passes the bookmark/start_date as the `from` filter."""
    stream = _get_stream("match_history", CONFIG)
    records = list(stream.get_records(context=None))
    assert len(records) == 2
    assert all(r["status"] == "completed" for r in records)
    assert all("tape" in r for r in records)
    call = next(c for c in mocked_api.calls if "/history/matches" in c.request.url)
    assert "from=2026-08-01T00%3A00%3A00Z" in call.request.url


def test_tour_filter_applied(mocked_api):
    """The optional `tour` setting is forwarded on match streams."""
    stream = _get_stream("fixtures", {**CONFIG, "tour": "atp"})
    list(stream.get_records(context=None))
    call = [c for c in mocked_api.calls if "/fixtures" in c.request.url][-1]
    assert "tour=atp" in call.request.url


def test_players_search_param(mocked_api):
    """player_search becomes the `search` query parameter."""
    stream = _get_stream("players", {**CONFIG, "player_search": "server"})
    list(stream.get_records(context=None))
    call = [c for c in mocked_api.calls if "/players" in c.request.url][-1]
    assert "search=server" in call.request.url


def test_upgrade_required_is_actionable(mocked_api):
    """A 403 upgrade_required fails loudly with a tier explanation."""
    mocked_api.add(
        responses.GET,
        "https://free-key.example.test/v1/history/matches",
        json={"error": "upgrade_required"},
        status=403,
    )
    stream = _get_stream(
        "match_history",
        {**CONFIG, "api_url": "https://free-key.example.test/v1"},
    )
    with pytest.raises(FatalAPIError, match="BASIC"):
        list(stream.get_records(context=None))
