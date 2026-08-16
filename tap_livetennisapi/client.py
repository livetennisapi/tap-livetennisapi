"""REST client handling for tap-livetennisapi."""

from __future__ import annotations

import typing as t

from singer_sdk.authenticators import BearerTokenAuthenticator
from singer_sdk.exceptions import FatalAPIError
from singer_sdk.pagination import BaseAPIPaginator, OffsetPaginator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    import requests

PAGE_SIZE = 200  # API maximum; fewest requests per sync (free tier: 100 req/day).


class LiveTennisPaginator(OffsetPaginator):
    """Offset paginator driven by the API's `meta.has_more` flag.

    Every list endpoint returns ``{"data": [...], "meta": {...}}`` where
    ``meta.has_more`` says whether results exist beyond this page. The API
    docs say to read that flag rather than comparing count to limit.
    """

    def has_more(self, response: requests.Response) -> bool:
        """Return True when the API reports more pages exist."""
        meta = response.json().get("meta") or {}
        return bool(meta.get("has_more"))


class LiveTennisAPIStream(RESTStream):
    """Base stream class for Live Tennis API streams."""

    records_jsonpath = "$.data[*]"

    @property
    def url_base(self) -> str:
        """Base URL, overridable via the `api_url` setting."""
        return self.config.get(
            "api_url", "https://api.livetennisapi.com/api/public/v1"
        )

    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """`Authorization: Bearer <api_key>` per the API's bearerAuth scheme."""
        return BearerTokenAuthenticator(token=self.config["api_key"])

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Return the limit/offset paginator."""
        return LiveTennisPaginator(start_value=0, page_size=PAGE_SIZE)

    def get_url_params(
        self,
        context: dict | None,
        next_page_token: int | None,
    ) -> dict[str, t.Any]:
        """Shared limit/offset (and optional tour filter) query parameters."""
        params: dict[str, t.Any] = {
            "limit": PAGE_SIZE,
            "offset": next_page_token or 0,
        }
        if self.config.get("tour"):
            params["tour"] = self.config["tour"]
        return params

    def validate_response(self, response: requests.Response) -> None:
        """Surface the API's explicit tier errors with a useful message.

        A call above the key's tier returns ``403 {"error": "upgrade_required"}``
        — never a silent empty result. Turn that into an actionable error.
        """
        if response.status_code == 403:
            try:
                error = (response.json() or {}).get("error")
            except ValueError:
                error = None
            if error == "upgrade_required":
                msg = (
                    f"403 upgrade_required for stream '{self.name}' "
                    f"({response.request.method} {response.request.url}): this "
                    "endpoint is above your API key's tier. The match_history "
                    "stream requires a BASIC (or higher) Live Tennis API key, "
                    "or any Historical Data API plan. "
                    "See https://livetennisapi.com/pricing"
                )
                raise FatalAPIError(msg)
        super().validate_response(response)
