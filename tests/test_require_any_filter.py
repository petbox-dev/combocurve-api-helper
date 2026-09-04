"""The shared at-least-one-filter guard for deletes the API refuses to run unfiltered.

Before `APIBase._require_any_filter`, this block was inlined at five sites in two
spellings, and both forwarded empty strings: `chosen_id=''` from an unresolved lookup
paired with a real `data_source` sent `?chosenID=&dataSource=...`, deleting on a filter
the caller never meant. These tests pin both halves -- that nothing is sent when every
filter is empty, and that an empty filter is dropped rather than forwarded.
"""

from typing import Any, Optional

import pytest
from requests.structures import CaseInsensitiveDict

from combocurve_api_helper import ComboCurveAPI
from combocurve_api_helper.base import APIBase

PROJECT_ID = '000000000000000000000001'
WELL_ID = '000000000000000000000002'
SCENARIO_ID = '000000000000000000000003'

# Every delete that guards on "at least one filter", with the keyword arguments that
# scope it and the caller-facing names its error message must list.
GUARDED_DELETES: list[tuple[str, tuple[str, ...], dict[str, str], str]] = [
    ('delete_company_wells', (), {'well_id': WELL_ID}, 'chosen_id, data_source, or well_id'),
    ('delete_project_company_wells', (PROJECT_ID,), {'well_id': WELL_ID}, 'chosen_id, data_source, or well_id'),
    ('delete_project_wells', (PROJECT_ID,), {'well_id': WELL_ID}, 'chosen_id, data_source, or well_id'),
    ('delete_scenarios', (PROJECT_ID,), {'scenario_id': WELL_ID}, 'scenario_name or scenario_id'),
    ('delete_type_curves', (PROJECT_ID,), {'id': WELL_ID}, 'name or id'),
]


class _StubResponse:
    """Stands in for the single `requests.Response` a delete returns."""

    def __init__(self) -> None:
        self.headers: CaseInsensitiveDict[str] = CaseInsensitiveDict({'X-Delete-Count': '1'})


def _recording_api() -> tuple[ComboCurveAPI, list[str]]:
    """A client that records delete urls instead of issuing requests, and needs no auth."""
    api = ComboCurveAPI.__new__(ComboCurveAPI)
    urls: list[str] = []

    def fake_delete_responses(url: str, data: Any, chunksize: Optional[int] = None) -> list[Any]:
        urls.append(url)
        return [_StubResponse()]

    api._delete_responses = fake_delete_responses  # type: ignore[method-assign]

    return api, urls


@pytest.mark.parametrize(('method', 'args', 'valid', 'parameters'), GUARDED_DELETES)
def test_no_filters_raises_and_sends_nothing(
    method: str, args: tuple[str, ...], valid: dict[str, str], parameters: str
) -> None:
    api, urls = _recording_api()

    with pytest.raises(ValueError, match=f'Must provide at least one of {parameters}'):
        getattr(api, method)(*args)

    assert urls == []


@pytest.mark.parametrize(('method', 'args', 'valid', 'parameters'), GUARDED_DELETES)
def test_all_filters_empty_raises_and_sends_nothing(
    method: str, args: tuple[str, ...], valid: dict[str, str], parameters: str
) -> None:
    """`''` must be refused, not forwarded -- the old `(a or b or c) is None` let it pass."""
    api, urls = _recording_api()
    empty = dict.fromkeys(valid, '')

    with pytest.raises(ValueError, match='Must provide at least one of'):
        getattr(api, method)(*args, **empty)

    assert urls == []


@pytest.mark.parametrize(('method', 'args', 'valid', 'parameters'), GUARDED_DELETES)
def test_a_single_valid_filter_is_enough(
    method: str, args: tuple[str, ...], valid: dict[str, str], parameters: str
) -> None:
    api, urls = _recording_api()

    headers = getattr(api, method)(*args, **valid)

    assert len(urls) == 1
    assert headers['X-Delete-Count'] == '1'


# The scenario sub-deletes take REQUIRED positional filter strings, so Python already
# refuses a missing filter; the guard's job is to refuse an EMPTY one that would issue an
# unscoped destructive delete. Each entry: method, args carrying an all-empty filter, args
# carrying a valid filter, and the full error-message regex the guard must raise.
SCENARIO_GUARDED_DELETES: list[tuple[str, tuple[str, ...], tuple[str, ...], str]] = [
    (
        'delete_scenario_wells',
        (PROJECT_ID, SCENARIO_ID, ''),
        (PROJECT_ID, SCENARIO_ID, WELL_ID),
        'Must provide at least one of wells',
    ),
    (
        'delete_scenario_combo',
        (PROJECT_ID, SCENARIO_ID, ''),
        (PROJECT_ID, SCENARIO_ID, 'saved'),
        'Must provide at least one of saved_name',
    ),
    (
        'delete_scenario_qualifiers',
        (PROJECT_ID, SCENARIO_ID, '', ''),
        (PROJECT_ID, SCENARIO_ID, 'oil', 'q1'),
        'Must provide both econ_names and qualifier_names',
    ),
]


@pytest.mark.parametrize(('method', 'empty_args', 'valid_args', 'message'), SCENARIO_GUARDED_DELETES)
def test_scenario_delete_empty_filter_raises_and_sends_nothing(
    method: str, empty_args: tuple[str, ...], valid_args: tuple[str, ...], message: str
) -> None:
    """An empty filter string on a scenario sub-delete is refused, not sent as `?key=`."""
    api, urls = _recording_api()

    with pytest.raises(ValueError, match=message):
        getattr(api, method)(*empty_args)

    assert urls == []


@pytest.mark.parametrize(('method', 'empty_args', 'valid_args', 'message'), SCENARIO_GUARDED_DELETES)
def test_scenario_delete_valid_filter_sends_one_request(
    method: str, empty_args: tuple[str, ...], valid_args: tuple[str, ...], message: str
) -> None:
    api, urls = _recording_api()

    getattr(api, method)(*valid_args)

    assert len(urls) == 1


@pytest.mark.parametrize('args', [(PROJECT_ID, SCENARIO_ID, '', 'q1'), (PROJECT_ID, SCENARIO_ID, 'oil', '')])
def test_scenario_qualifiers_mixed_empty_is_refused(args: tuple[str, ...]) -> None:
    """A partially-unresolved lookup ('' in ONE field) must not forward a blank filter
    alongside a real one -- both econNames and qualifierNames are required by the API, so
    a blank either could widen the delete if the API reads it as "unfiltered"."""
    api, urls = _recording_api()

    with pytest.raises(ValueError, match='Must provide both econ_names and qualifier_names'):
        api.delete_scenario_qualifiers(*args)

    assert urls == []


@pytest.mark.parametrize('method', ['delete_company_wells', 'delete_project_company_wells', 'delete_project_wells'])
def test_an_empty_filter_is_dropped_not_forwarded(method: str) -> None:
    """The specific hazard: an empty value alongside a real one must not reach the query.

    Covers all three sibling well deletes that share the `chosen_id`/`data_source`/`well_id`
    guard, not just `delete_company_wells` -- a regression in any one of them would forward
    `?chosenID=&dataSource=internal` and pass a single-method test.
    """
    api, urls = _recording_api()
    args = () if method == 'delete_company_wells' else (PROJECT_ID,)

    getattr(api, method)(*args, chosen_id='', data_source='internal')

    assert 'chosenID' not in urls[0]
    assert urls[0].endswith('?dataSource=internal')


def test_delete_company_wells_filters_are_keyword_only() -> None:
    """A stale positional `delete_company_wells(project_id)` must raise, not silently rebind.

    All three filters are `Optional[str]`, so a positional argument would otherwise bind to
    `chosen_id` and issue a real, differently-scoped DELETE. The `*` makes it a `TypeError`.
    """
    api, _urls = _recording_api()

    with pytest.raises(TypeError):
        api.delete_company_wells(WELL_ID)  # type: ignore[call-arg]


def test_helper_keys_the_result_by_api_name_and_reports_parameter_names() -> None:
    assert APIBase._require_any_filter({'chosenID': 'A', 'dataSource': None}, 'x or y') == {'chosenID': 'A'}

    with pytest.raises(ValueError, match='Must provide at least one of chosen_id, data_source, or well_id'):
        APIBase._require_any_filter(
            {'chosenID': None, 'dataSource': '', 'id': None},
            'chosen_id, data_source, or well_id',
        )
