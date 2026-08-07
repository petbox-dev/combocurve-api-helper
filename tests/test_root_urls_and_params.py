"""Unit tests for root route paths and query-parameter assembly -- no live API.

Two defects motivated these, both live-verified against api.combocurve.com on
2026-08-06 and both silent under the type checker:

1. Three root routes were spelled wrong and 404'd with the Google-ESP body
   `{"code": 5, "message": "Method does not exist."}` -- the ROOT forecast volume
   routes are flat and hyphenated (`/v1/forecast-monthly-volumes`), only the
   PROJECT-scoped pair nests under `forecasts/`; and well identifiers is plural
   (`/v1/wells-identifiers`). Both spellings are confirmed by the Postman
   collection and the OpenAPI spec (`operationId: get-root-forecast-monthly-volumes`,
   `patch-wells-identifiers`).

2. Query parameters arrive through two channels that `requests` appends rather
   than merges, so a `take` in `filters` collided with the api method's
   `{'take': GET_LIMIT}` and produced `?take=None&take=200` -- rejected by the API
   as `TypeError: `None,200` is not a valid number`.
"""

from typing import Any, Optional, cast

import pytest
import requests
from pytest import MonkeyPatch

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import APIBase, _drop_params_already_in_url

V1 = 'https://api.combocurve.com/v1'


class _FakeResponse:
    """Minimal stand-in for requests.Response carrying no next-page Link header."""

    def __init__(self, body: Any) -> None:
        self.status_code = 200
        self._body = body
        self.headers: dict[str, str] = {}

    def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        return None


class _StubAuth:
    """Stands in for ComboCurveAuth; the transport only ever asks it for headers."""

    def get_auth_headers(self) -> dict[str, str]:
        return {}


def _make_api() -> ComboCurveAPI:
    """A client with no credentials read from disk.

    `ComboCurveAPI()` runs `ServiceAccount.from_file(...)`, so constructing one makes
    these tests unrunnable without `~/.combocurve/combocurve.json` -- exactly the CI
    machine where a 404-route regression is cheapest to catch. Nothing here needs auth,
    so `__new__` skips `APIBase.__init__` and a stub supplies the one method the request
    path calls. Matches the policy `tests/test_production_delete.py` states.
    """
    api = ComboCurveAPI.__new__(ComboCurveAPI)
    api.auth = _StubAuth()

    return api


def _capture_requests(monkeypatch: MonkeyPatch) -> list[tuple[str, Any]]:
    """Record every (url, params) pair `_request_with_retry` dispatches."""
    calls: list[tuple[str, Any]] = []

    def fake_request(method: str, url: str, **kwargs: Any) -> _FakeResponse:
        calls.append((url, kwargs.get('params')))
        return _FakeResponse([])

    monkeypatch.setattr(requests, 'request', fake_request)
    return calls


###############
# route paths #
###############


def test_root_volume_url_builders_are_flat_and_hyphenated() -> None:
    """The nested `forecasts/` spelling is the project-scoped route; at root it 404s."""
    api = _make_api()
    assert api.get_root_forecast_monthly_volumes_url() == f'{V1}/forecast-monthly-volumes'
    assert api.get_root_forecast_daily_volumes_url() == f'{V1}/forecast-daily-volumes'


def test_project_scoped_volume_urls_still_nest() -> None:
    """Guard the other half of the distinction: these SHOULD nest under forecasts/."""
    api = _make_api()
    assert api.get_forecast_monthly_volumes_url('P', 'F') == f'{V1}/projects/P/forecasts/F/monthly-volumes'
    assert api.get_forecast_daily_volumes_url('P', 'F') == f'{V1}/projects/P/forecasts/F/daily-volumes'


def test_well_identifiers_url_is_plural() -> None:
    assert _make_api().get_well_identifiers_url() == f'{V1}/wells-identifiers'


###############################
# required volume scope guard #
###############################


@pytest.mark.parametrize(
    'method',
    ['get_root_forecast_monthly_volumes', 'get_root_forecast_daily_volumes'],
)
@pytest.mark.parametrize('filters', [None, {}, {'take': '5'}, {'forecast': ''}])
def test_unscoped_volume_request_is_refused(
    monkeypatch: MonkeyPatch, method: str, filters: Optional[dict[str, str]]
) -> None:
    """The API 400s without project/forecast/well, so it never leaves the process."""
    api = _make_api()
    calls = _capture_requests(monkeypatch)

    with pytest.raises(ValueError, match='at least one of project, forecast, well'):
        getattr(api, method)(filters)

    assert calls == []


@pytest.mark.parametrize('scope', ['project', 'forecast', 'well'])
def test_any_one_scope_filter_is_accepted(monkeypatch: MonkeyPatch, scope: str) -> None:
    api = _make_api()
    calls = _capture_requests(monkeypatch)

    api.get_root_forecast_monthly_volumes({scope: 'X'})

    assert calls[0] == (f'{V1}/forecast-monthly-volumes?{scope}=X', {'take': 200})


#########################
# _build_params_string  #
#########################


def test_build_params_string_empty_yields_no_query() -> None:
    assert APIBase._build_params_string(None) == ''
    assert APIBase._build_params_string({}) == ''


def test_build_params_string_drops_none_values() -> None:
    """`None` must be omitted, not rendered as the literal text `None`."""
    assert APIBase._build_params_string({'take': None}) == ''
    assert APIBase._build_params_string({'forecast': 'F', 'take': None}) == '?forecast=F'


def test_build_params_string_percent_encodes_values() -> None:
    """`&`/`=`/`#` are encoded; a space becomes `%20`, NOT the `urlencode` default `+`."""
    assert APIBase._build_params_string({'name': 'a&b=c d'}) == '?name=a%26b%3Dc%20d'
    assert APIBase._build_params_string({'name': 'a#b'}) == '?name=a%23b'


def test_build_params_string_leaves_commas_literal() -> None:
    """List filters are comma-joined and were live-verified unencoded; keep them that way.

    `econ_runs` `columns`, `_econ_model_base` `wells` and `scenarios` `econNames` all
    build `a,b,c`. Encoding the separator to `%2C` would change requests that are known
    to work, and `,` is a legal unencoded query character (RFC 3986 sub-delim).
    """
    assert APIBase._build_params_string({'columns': 'gross_oil,net_income'}) == '?columns=gross_oil,net_income'


def test_build_params_string_keeps_multiple_filters_in_order() -> None:
    assert APIBase._build_params_string({'project': 'P', 'forecast': 'F'}) == '?project=P&forecast=F'


##############################
# two-channel param dedupe   #
##############################


def test_filters_take_wins_over_the_method_default(monkeypatch: MonkeyPatch) -> None:
    """A caller-supplied `take` must not be duplicated by `{'take': GET_LIMIT}`."""
    api = _make_api()
    calls = _capture_requests(monkeypatch)

    api.get_root_forecast_monthly_volumes({'forecast': 'F', 'take': '50'})

    # The exact url pins it: `take` appears once, carrying the caller's value.
    assert calls[0] == (f'{V1}/forecast-monthly-volumes?forecast=F&take=50', {})


def test_none_take_falls_back_to_the_method_default(monkeypatch: MonkeyPatch) -> None:
    """`{'take': None}` drops out of the url, so GET_LIMIT still applies -- once.

    A `None` filter value is OUTSIDE the declared `dict[str, str]` contract -- mypy
    rejects it, hence the cast -- but untyped callers reach the API this way, and the
    old f-string rendered it as the literal text `None`. This pins the runtime
    tolerance, it does not bless `None` as a supported filter value.
    """
    api = _make_api()
    calls = _capture_requests(monkeypatch)

    api.get_root_forecast_monthly_volumes(cast('dict[str, str]', {'forecast': 'F', 'take': None}))

    (url, params) = calls[0]
    assert url == f'{V1}/forecast-monthly-volumes?forecast=F'
    assert params == {'take': 200}


def test_a_valueless_query_key_still_counts_as_present() -> None:
    """`?take=` must suppress the default too -- this is what `keep_blank_values` buys.

    Without the flag `parse_qsl` discards blank pairs, the key reads as absent, and
    `?take=&take=200` goes out: the duplicate-key bug for that spelling.
    """
    assert _drop_params_already_in_url('https://x/y?take=', {'take': 200}) == {}
    assert _drop_params_already_in_url('https://x/y?forecast=', {'take': 200}) == {'take': 200}


def test_unrelated_params_survive_the_dedupe(monkeypatch: MonkeyPatch) -> None:
    api = _make_api()
    calls = _capture_requests(monkeypatch)

    api.get_root_forecast_monthly_volumes({'forecast': 'F'})

    assert calls[0] == (f'{V1}/forecast-monthly-volumes?forecast=F', {'take': 200})


def test_dedupe_is_a_noop_without_a_query_string(monkeypatch: MonkeyPatch) -> None:
    api = _make_api()
    calls = _capture_requests(monkeypatch)

    api.get_root_econ_runs()

    assert calls[0] == (f'{V1}/econ-runs', {'take': 200})
