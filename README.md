# tap-livetennisapi

`tap-livetennisapi` is a [Singer](https://www.singer.io/) tap for the
[Live Tennis API](https://livetennisapi.com), built with the
[Meltano Singer SDK](https://sdk.meltano.com).

It extracts tennis data — players, upcoming fixtures, live matches and
(on a paid key) completed-match history — for loading into any Singer
target or a [Meltano](https://meltano.com) pipeline.

- API docs: https://docs.livetennisapi.com (OpenAPI: https://docs.livetennisapi.com/openapi.yaml)
- Coverage: every tour equally — ATP, WTA, Challenger, ITF and juniors
  (boys' and girls' Grand Slam draws)
- This tap is not distributed on PyPI; install it from Git (below)

## Streams

| Stream | Endpoint | Tier | Replication | Primary key |
| ------ | -------- | ---- | ----------- | ----------- |
| `players` | `GET /players` | FREE | FULL_TABLE | `id` |
| `fixtures` | `GET /fixtures` | FREE | FULL_TABLE | `id` |
| `live_matches` | `GET /matches?status=live` | FREE | FULL_TABLE | `id` |
| `match_history` | `GET /history/matches` | **BASIC+** | INCREMENTAL (`scheduled_time`) | `id` |

Replication notes (honest ones):

- **`fixtures`** exposes only the *upcoming* schedule, earliest first, with
  no date-range or updated-since cursor — so it is a FULL_TABLE snapshot by
  design. Rows leave the feed as matches start; re-sync it daily and treat
  each run as the current forward-looking schedule.
- **`live_matches`** is a point-in-time snapshot of matches in play right
  now. FULL_TABLE, replaced every run.
- **`match_history`** is the only stream with a real server-side cursor: the
  endpoint accepts a `from` play-date filter, which the tap drives from the
  Singer bookmark (initially from `start_date`). The API returns newest
  first, so the stream is declared unsorted and the bookmark is finalized at
  the end of a successful sync. The completed-match tape starts January 2023;
  deeper results (1968–2022) live in the archive endpoints, which this tap
  does not cover.
- **`players`** is a search/list surface with no change cursor: FULL_TABLE.
  Set `player_search` to restrict it to a name search; without it you get
  the unfiltered listing, ranked players first.

### `match_history` requires a paid key

`/history/matches` is part of the paid History product. It requires **BASIC
or higher** on the Live Tennis API, or any
[Historical Data API](https://livetennisapi.com/historical-tennis-data-api)
plan. On a FREE key the API returns `403 {"error": "upgrade_required"}` —
never a silent empty result — and the tap fails with an actionable message.
Deselect the stream in your catalog if you run on a free key.

## Quotas — will this fit the free tier?

Free tier: **30 requests/minute, 100 requests/day** (self-serve, no card:
https://livetennisapi.com/subscribe/free). The tap requests the maximum page
size (200 rows/request), so a daily sync of the three free streams is
typically a handful of requests — **daily fixture/live/player syncs fit the
free tier comfortably**. The history stream's backfill volume depends on
your `start_date`; BASIC is 60 req/min, 1,000/day. The tap honours the API's
`429` responses via the SDK's built-in backoff-and-retry.

## Configuration

| Setting | Required | Description |
| ------- | -------- | ----------- |
| `api_key` | yes | API key, sent as `Authorization: Bearer <key>`. |
| `start_date` | no | Earliest play date for `match_history` (ISO-8601). The tape starts 2023-01-01. |
| `tour` | no | Filter `fixtures`/`live_matches`/`match_history` to one tour: `atp`, `wta`, `challenger`, `itf`, `juniors` (each value includes its doubles draws). |
| `player_search` | no | Name search for the `players` stream. |
| `api_url` | no | Base URL override (default `https://api.livetennisapi.com/api/public/v1`). |

A full list, including the SDK's built-in stream-map and flattening
settings, is available via `tap-livetennisapi --about`.

## Installation

```bash
pipx install git+https://github.com/livetennisapi/tap-livetennisapi.git
# or
pip install git+https://github.com/livetennisapi/tap-livetennisapi.git
```

### With Meltano

```yaml
# meltano.yml
plugins:
  extractors:
    - name: tap-livetennisapi
      namespace: tap_livetennisapi
      pip_url: git+https://github.com/livetennisapi/tap-livetennisapi.git
      executable: tap-livetennisapi
      capabilities: [catalog, state, discover, about, stream-maps, schema-flattening]
      settings:
        - name: api_key
          kind: password
        - name: start_date
          kind: date_iso8601
        - name: tour
        - name: player_search
        - name: api_url
      config:
        start_date: "2026-01-01T00:00:00Z"
```

```bash
meltano add extractor tap-livetennisapi
meltano config tap-livetennisapi set api_key <your-key>
meltano run tap-livetennisapi target-jsonl
```

## Usage (standalone)

```bash
tap-livetennisapi --version
tap-livetennisapi --about
tap-livetennisapi --config config.json --discover > catalog.json
tap-livetennisapi --config config.json --catalog catalog.json
```

`config.json`:

```json
{
  "api_key": "ltapi_xxx",
  "start_date": "2026-01-01T00:00:00Z"
}
```

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
```

Tests use the Singer SDK's built-in tap test framework with fully mocked
HTTP responses (the `responses` library) — no network and no API key are
needed to run them.

## License

MIT — see [LICENSE](LICENSE).
