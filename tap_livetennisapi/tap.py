"""TapLiveTennisAPI tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_livetennisapi import streams


class TapLiveTennisAPI(Tap):
    """Singer tap for the Live Tennis API (livetennisapi.com)."""

    name = "tap-livetennisapi"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_key",
            th.StringType,
            required=True,
            secret=True,
            title="API Key",
            description=(
                "Live Tennis API key, sent as `Authorization: Bearer <key>`. "
                "A free key is self-serve at https://livetennisapi.com/subscribe/free "
                "(30 requests/minute, 100/day). The match_history stream needs "
                "a BASIC or higher key, or any Historical Data API plan."
            ),
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            title="Start Date",
            description=(
                "Earliest play date for the match_history stream's incremental "
                "`from` filter (ISO-8601). The completed-match tape starts "
                "January 2023. Ignored by the players, fixtures and "
                "live_matches streams, which are point-in-time surfaces."
            ),
        ),
        th.Property(
            "tour",
            th.StringType,
            allowed_values=["atp", "wta", "challenger", "itf", "juniors"],
            title="Tour",
            description=(
                "Optional tour filter applied to the fixtures, live_matches and "
                "match_history streams (the API's grouped vocabulary; each value "
                "includes its doubles draws). Omit for all tours."
            ),
        ),
        th.Property(
            "player_search",
            th.StringType,
            title="Player Search",
            description=(
                "Optional name search for the players stream (the `search` "
                "query parameter of GET /players). Omit to sync the unfiltered "
                "player listing, ranked players first."
            ),
        ),
        th.Property(
            "api_url",
            th.StringType,
            default="https://api.livetennisapi.com/api/public/v1",
            title="API URL",
            description="Base URL of the Live Tennis API (override for testing).",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.LiveTennisAPIStream]:
        """Return a list of discovered streams."""
        return [
            streams.PlayersStream(self),
            streams.FixturesStream(self),
            streams.LiveMatchesStream(self),
            streams.MatchHistoryStream(self),
        ]


if __name__ == "__main__":
    TapLiveTennisAPI.cli()
