"""Stream classes for tap-livetennisapi.

Schemas mirror the published OpenAPI document at
https://docs.livetennisapi.com/openapi.yaml (v1.3.1). No fields are invented;
nullable fields are nullable because the API documents them as real states.
"""

from __future__ import annotations

import typing as t

from singer_sdk import typing as th

from tap_livetennisapi.client import LiveTennisAPIStream

# ---------------------------------------------------------------------------
# Shared schema fragments (from components/schemas in the OpenAPI spec)
# ---------------------------------------------------------------------------

# Player object as returned in list payloads and embedded in matches.
# `stats` exists only on the single-player endpoint, which this tap does not
# call, so it is deliberately not declared here.
PLAYER_OBJECT = th.ObjectType(
    th.Property("id", th.IntegerType),
    th.Property(
        "tour",
        th.StringType,
        description=(
            "The record's OWN tour label (granular, e.g. 'juniors_boys'); "
            "NOT the grouped `tour` filter vocabulary. Opaque string."
        ),
    ),
    th.Property("name", th.StringType),
    th.Property("country", th.StringType),
    th.Property("ranking", th.IntegerType),
    th.Property("ranking_points", th.IntegerType),
    th.Property("ranking_movement", th.StringType),
    th.Property("hand", th.StringType),
    th.Property("backhand", th.IntegerType),
    th.Property("birthday", th.DateType),
    th.Property("is_doubles_team", th.BooleanType),
    th.Property(
        "data_completeness",
        th.ObjectType(
            th.Property("known", th.IntegerType),
            th.Property("of", th.IntegerType),
            th.Property("missing", th.ArrayType(th.StringType)),
            th.Property("note", th.StringType),
        ),
    ),
)

# Score object; win_probability_p1/danger are ULTRA-only and null below that
# tier. `points` entries can be null (observed live on completed matches).
SCORE_OBJECT = th.ObjectType(
    th.Property("sets", th.ArrayType(th.IntegerType)),
    th.Property("games", th.ArrayType(th.ArrayType(th.IntegerType))),
    th.Property("points", th.ArrayType(th.StringType)),
    th.Property("server", th.IntegerType),
    th.Property("is_tiebreak", th.BooleanType),
    th.Property("win_probability_p1", th.NumberType),
    th.Property("danger", th.NumberType),
    th.Property("timestamp", th.DateTimeType),
)

# Properties shared by Match and HistoryMatch (HistoryMatch = Match + tape).
MATCH_PROPERTIES: list[th.Property] = [
    th.Property("id", th.IntegerType, required=True),
    th.Property("tournament", th.StringType),
    th.Property(
        "tour",
        th.StringType,
        description="Grouped tour vocabulary (atp/wta/challenger/itf/juniors) or null.",
    ),
    th.Property("tournament_id", th.StringType),
    th.Property("surface", th.StringType),
    th.Property("indoor", th.BooleanType),
    th.Property("format", th.StringType),
    th.Property("round", th.StringType),
    th.Property("round_code", th.StringType),
    th.Property("status", th.StringType),
    th.Property("event_status", th.StringType),
    th.Property("is_doubles", th.BooleanType),
    th.Property("scheduled_time", th.DateTimeType),
    th.Property(
        "players",
        th.ObjectType(
            th.Property("p1", PLAYER_OBJECT),
            th.Property("p2", PLAYER_OBJECT),
        ),
    ),
    th.Property("score", SCORE_OBJECT),
    th.Property("winner", th.IntegerType),
    th.Property("withdrew", th.IntegerType),
]


# ---------------------------------------------------------------------------
# Streams
# ---------------------------------------------------------------------------


class PlayersStream(LiveTennisAPIStream):
    """Players from GET /players (FREE tier).

    Ranked players first. The endpoint is a search/list surface with no
    change cursor, so replication is FULL_TABLE. Set the optional
    `player_search` setting to restrict results to a name search.
    """

    name = "players"
    path = "/players"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_method = "FULL_TABLE"
    replication_key = None
    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, required=True),
        th.Property("name", th.StringType),
        th.Property("tour", th.StringType),
        th.Property("country", th.StringType),
        th.Property("ranking", th.IntegerType),
        th.Property("ranking_points", th.IntegerType),
        th.Property("ranking_movement", th.StringType),
        th.Property("hand", th.StringType),
        th.Property("backhand", th.IntegerType),
        th.Property("birthday", th.DateType),
        th.Property("is_doubles_team", th.BooleanType),
        th.Property(
            "data_completeness",
            th.ObjectType(
                th.Property("known", th.IntegerType),
                th.Property("of", th.IntegerType),
                th.Property("missing", th.ArrayType(th.StringType)),
                th.Property("note", th.StringType),
            ),
        ),
    ).to_dict()

    def get_url_params(
        self,
        context: dict | None,
        next_page_token: int | None,
    ) -> dict[str, t.Any]:
        """Add the optional `search` term; /players takes no `tour` filter."""
        params: dict[str, t.Any] = {
            "limit": 200,
            "offset": next_page_token or 0,
        }
        if self.config.get("player_search"):
            params["search"] = self.config["player_search"]
        return params


class FixturesStream(LiveTennisAPIStream):
    """Upcoming scheduled fixtures from GET /fixtures (FREE tier).

    The endpoint returns only upcoming fixtures, earliest first, and offers
    no date-range or updated-since cursor — so replication is honestly
    FULL_TABLE: each run re-reads the current forward-looking schedule.
    That is the correct semantic for a schedule (rows leave the feed as
    matches start), and a daily full sync fits comfortably inside the free
    tier's 100 requests/day.
    """

    name = "fixtures"
    path = "/fixtures"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_method = "FULL_TABLE"
    replication_key = None
    schema = th.PropertiesList(
        th.Property("id", th.IntegerType, required=True),
        th.Property("event_date", th.DateType),
        th.Property(
            "start_time",
            th.DateTimeType,
            description="Scheduled start (UTC). Null until the order of play assigns a time.",
        ),
        th.Property(
            "player1_id",
            th.IntegerType,
            description="Roster player id; null when unresolved (names always present).",
        ),
        th.Property("player2_id", th.IntegerType),
        th.Property(
            "tour",
            th.StringType,
            description="The record's OWN granular tour label; opaque string.",
        ),
        th.Property("tournament", th.StringType),
        th.Property("round", th.StringType),
        th.Property("round_code", th.StringType),
        th.Property("surface", th.StringType),
        th.Property("player1_name", th.StringType),
        th.Property("player2_name", th.StringType),
        th.Property("status", th.StringType),
    ).to_dict()


class LiveMatchesStream(LiveTennisAPIStream):
    """Matches currently in play, from GET /matches?status=live (FREE tier).

    A live snapshot by definition: the set of rows is the set of matches in
    play at request time, so replication is FULL_TABLE (each run replaces
    the snapshot). Not a history surface — completed matches belong to the
    match_history stream.
    """

    name = "live_matches"
    path = "/matches"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_method = "FULL_TABLE"
    replication_key = None
    schema = th.PropertiesList(*MATCH_PROPERTIES).to_dict()

    def get_url_params(
        self,
        context: dict | None,
        next_page_token: int | None,
    ) -> dict[str, t.Any]:
        """Pin status=live on top of the shared parameters."""
        params = super().get_url_params(context, next_page_token)
        params["status"] = "live"
        return params


class MatchHistoryStream(LiveTennisAPIStream):
    """Completed matches from GET /history/matches.

    REQUIRES A PAID KEY: BASIC (or higher) on the Live Tennis API, or any
    Historical Data API plan. On a FREE key the API returns
    403 {"error": "upgrade_required"} — never a silent empty result — and
    this tap fails loudly with an actionable message.

    Replication is INCREMENTAL on `scheduled_time`: the endpoint accepts a
    `from` play-date filter (YYYY-MM-DD or ISO-8601 datetime), which the tap
    sets from the stream bookmark (falling back to the `start_date` setting).
    The API returns newest-first, so the stream is declared unsorted and the
    bookmark is finalized only when a sync completes. Each record also
    carries the `tape` object describing point-by-point coverage.
    """

    name = "match_history"
    path = "/history/matches"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_method = "INCREMENTAL"
    replication_key = "scheduled_time"
    is_sorted = False
    schema = th.PropertiesList(
        *MATCH_PROPERTIES,
        th.Property(
            "tape",
            th.ObjectType(
                th.Property("coverage", th.StringType),
                th.Property("rows", th.IntegerType),
                th.Property("reconstructed_rows", th.IntegerType),
                th.Property("model_rows", th.IntegerType),
            ),
            description="What point-by-point data the API holds for this match.",
        ),
    ).to_dict()

    def get_url_params(
        self,
        context: dict | None,
        next_page_token: int | None,
    ) -> dict[str, t.Any]:
        """Add the `from` play-date filter from the bookmark / start_date."""
        params = super().get_url_params(context, next_page_token)
        starting_ts = self.get_starting_timestamp(context)
        if starting_ts is not None:
            # `from`: a bare date covers that whole day; datetimes accepted.
            params["from"] = starting_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return params
