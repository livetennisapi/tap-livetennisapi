"""Shared test fixtures: every HTTP call is mocked; no network is used.

The mock payloads mirror the shapes documented in the published OpenAPI
document (https://docs.livetennisapi.com/openapi.yaml, v1.3.1): list
endpoints return ``{"data": [...], "meta": {...}}`` and meta carries the
``has_more`` paging flag.
"""

from __future__ import annotations

import pytest
import responses

API_BASE = "https://api.livetennisapi.com/api/public/v1"


def _meta(count: int) -> dict:
    return {
        "limit": 200,
        "offset": 0,
        "count": count,
        "total": count,
        "has_more": False,
    }


def _player(pid: int, name: str, tour: str, country: str, ranking: int) -> dict:
    return {
        "id": pid,
        "name": name,
        "tour": tour,
        "country": country,
        "ranking": ranking,
        "ranking_points": 5000 - pid,
        "ranking_movement": "same",
        "hand": "R",
        "backhand": 2,
        "birthday": "2001-05-31",
        "is_doubles_team": False,
        "data_completeness": {
            "known": 4,
            "of": 4,
            "missing": [],
        },
    }


PLAYERS_PAYLOAD = {
    "data": [
        _player(101, "Ace Server", "atp", "sui", 3),
        _player(102, "Drop Shotter", "wta", "pol", 2),
    ],
    "meta": _meta(2),
}

FIXTURES_PAYLOAD = {
    "data": [
        {
            "id": 501,
            "event_date": "2026-08-17",
            "start_time": "2026-08-17T11:00:00Z",
            "player1_id": 101,
            "player2_id": None,
            "tour": "atp",
            "tournament": "Cincinnati Open",
            "round": "Quarterfinal",
            "round_code": "QF",
            "surface": "hard",
            "player1_name": "Ace Server",
            "player2_name": "Net Rusher",
            "status": "upcoming",
        },
        {
            # A date-only fixture is a real state (start_time null until the
            # order of play assigns a time), per the OpenAPI description.
            "id": 502,
            "event_date": "2026-08-18",
            "start_time": None,
            "player1_id": None,
            "player2_id": None,
            "tour": "juniors_boys",
            "tournament": "US Open Juniors",
            "round": None,
            "round_code": None,
            "surface": "hard",
            "player1_name": "Junior One",
            "player2_name": "Junior Two",
            "status": "upcoming",
        },
    ],
    "meta": _meta(2),
}


def _match(mid: int, status: str, scheduled_time: str | None) -> dict:
    completed = status == "completed"
    return {
        "id": mid,
        "tournament": "Cincinnati Open",
        "tour": "atp",
        "tournament_id": "cincinnati-atp",
        "surface": "hard",
        "indoor": False,
        "format": "BO3",
        "round": "Round of 16",
        "round_code": "R16",
        "status": status,
        "event_status": None,
        "is_doubles": False,
        "scheduled_time": scheduled_time,
        "players": {
            "p1": _player(101, "Ace Server", "atp", "sui", 3),
            "p2": _player(103, "Base Liner", "atp", "esp", 7),
        },
        "score": {
            "sets": [1, 0] if not completed else [2, 0],
            "games": [[6, 4], [3, 2]] if not completed else [[6, 6], [4, 4]],
            "points": ["30", "15"] if not completed else [],
            "server": 1 if not completed else None,
            "is_tiebreak": False,
            "win_probability_p1": None,
            "danger": None,
            "timestamp": "2026-08-16T15:45:12Z",
        },
        "winner": 1 if completed else None,
        "withdrew": None,
    }


LIVE_MATCHES_PAYLOAD = {
    "data": [_match(9001, "live", "2026-08-16T15:00:00Z")],
    "meta": _meta(1),
}

HISTORY_PAYLOAD = {
    "data": [
        {
            **_match(8002, "completed", "2026-08-14T12:00:00Z"),
            "tape": {
                "coverage": "from_start",
                "rows": 142,
                "reconstructed_rows": 0,
                "model_rows": 140,
            },
        },
        {
            **_match(8001, "completed", "2026-08-13T10:00:00Z"),
            "tape": {
                "coverage": "reconstructed",
                "rows": 0,
                "reconstructed_rows": 120,
                "model_rows": 0,
            },
        },
    ],
    "meta": _meta(2),
}


def register_endpoints(rsps: responses.RequestsMock) -> None:
    """Register the mocked API surface (URLs without query match any query)."""
    rsps.add(responses.GET, f"{API_BASE}/players", json=PLAYERS_PAYLOAD)
    rsps.add(responses.GET, f"{API_BASE}/fixtures", json=FIXTURES_PAYLOAD)
    rsps.add(responses.GET, f"{API_BASE}/matches", json=LIVE_MATCHES_PAYLOAD)
    rsps.add(responses.GET, f"{API_BASE}/history/matches", json=HISTORY_PAYLOAD)


@pytest.fixture(scope="session", autouse=True)
def mocked_api():
    """Mock the whole API for every test; unregistered URLs hard-fail."""
    rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
    rsps.start()
    register_endpoints(rsps)
    yield rsps
    rsps.stop()
    rsps.reset()
