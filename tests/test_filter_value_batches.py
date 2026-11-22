"""`APIBase._filter_value_batches` refuses `skip`/`cursor` on a split, and the shared batch helpers
`_get_items_in_value_batches` / `_count_items_in_value_batches` -- offline, through a recording transport."""

from typing import Optional

import pytest
from pytest import MonkeyPatch

from combocurve_api_helper.base import WELL_FILTER_LIMIT, APIBase, WellFilters
from tests.http_fakes import V1, FakeResponse, install_recording_transport, make_offline_api

URL = f'{V1}/monthly-productions'


def well_ids(count: int) -> list[str]:
    """`count` distinct 24-hex ObjectId-like strings."""
    return [f'{index:024x}' for index in range(1, count + 1)]


def values_in(url: str, key: str) -> list[str]:
    """The values of the repeated `key` parameter of a url, in the order sent."""
    query = url.split('?', 1)[1] if '?' in url else ''
    return [pair.split('=', 1)[1] for pair in query.split('&') if pair.startswith(f'{key}=')]


def build_url(filters: Optional[WellFilters]) -> str:
    """The url builder the helpers are given: the route plus the batch's filters."""
    return URL + APIBase._build_params_string(filters)


@pytest.mark.parametrize('paging_key', ['skip', 'cursor'])
def test_split_refuses_a_paging_filter(paging_key: str) -> None:
    filters: WellFilters = {'well': well_ids(WELL_FILTER_LIMIT + 1), paging_key: '10'}

    with pytest.raises(ValueError, match=rf"'{paging_key}' cannot be combined with more than 100 distinct 'well'"):
        APIBase._filter_value_batches(filters, 'well')


@pytest.mark.parametrize('paging_key', ['skip', 'cursor'])
def test_single_batch_keeps_a_paging_filter(paging_key: str) -> None:
    filters: WellFilters = {'well': well_ids(WELL_FILTER_LIMIT), paging_key: '10'}

    assert APIBase._filter_value_batches(filters, 'well') == [filters]


def test_duplicates_that_fit_one_batch_keep_a_paging_filter() -> None:
    """The list is longer than the limit only through repeats, so de-duplication leaves one batch."""
    wells = well_ids(WELL_FILTER_LIMIT) + well_ids(1)
    filters: WellFilters = {'well': wells, 'skip': '10'}

    batches = APIBase._filter_value_batches(filters, 'well')

    assert len(batches) == 1


def test_split_refusal_is_before_any_request(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch)
    api = make_offline_api()

    with pytest.raises(ValueError, match='skip'):
        api._get_items_in_value_batches(build_url, {'well': well_ids(150), 'skip': '10'}, 'well')
    with pytest.raises(ValueError, match='cursor'):
        api._count_items_in_value_batches(build_url, {'well': well_ids(150), 'cursor': 'abc'}, 'well')

    assert recorder.calls == []


def test_split_with_a_none_paging_filter_is_allowed() -> None:
    """`_build_params_string` drops a None value, so it is not sent and does not count as present."""
    filters = {'well': well_ids(150), 'skip': None}

    assert len(APIBase._filter_value_batches(filters, 'well')) == 2


@pytest.mark.parametrize('skip', [0, '0'])
def test_split_allows_a_skip_of_zero(skip: object) -> None:
    """`skip=0` skips nothing, so the split is not refused; each batch carries it."""
    filters = {'well': well_ids(150), 'skip': skip}

    batches = APIBase._filter_value_batches(filters, 'well')  # type: ignore[arg-type]

    assert [batch['skip'] if batch else None for batch in batches] == [skip, skip]


def test_split_still_refuses_a_cursor_of_zero() -> None:
    with pytest.raises(ValueError, match="'cursor' cannot be combined"):
        APIBase._filter_value_batches({'well': well_ids(150), 'cursor': '0'}, 'well')


def test_get_items_in_value_batches_concatenates_rows_in_request_order(monkeypatch: MonkeyPatch) -> None:
    wells = well_ids(250)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, [{'well': wells[0]}]),
        FakeResponse(200, [{'well': wells[100]}, {'well': wells[101]}]),
        FakeResponse(200, []),
    )
    api = make_offline_api()

    rows = api._get_items_in_value_batches(build_url, {'well': wells}, 'well', {'take': 200})

    assert rows == [{'well': wells[0]}, {'well': wells[100]}, {'well': wells[101]}]
    assert [values_in(call.url, 'well') for call in recorder.calls] == [wells[:100], wells[100:200], wells[200:]]
    assert [call.params for call in recorder.calls] == [{'take': 200}] * 3


def test_get_items_in_value_batches_sends_one_request_for_no_filters(monkeypatch: MonkeyPatch) -> None:
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, [{'id': 'a'}]))
    api = make_offline_api()

    assert api._get_items_in_value_batches(build_url, None, 'well') == [{'id': 'a'}]
    assert [call.url for call in recorder.calls] == [URL]
    assert recorder.calls[0].params is None


def test_get_items_in_value_batches_deduplicates_values(monkeypatch: MonkeyPatch) -> None:
    wells = well_ids(150)
    recorder = install_recording_transport(monkeypatch, FakeResponse(200, []), FakeResponse(200, []))
    api = make_offline_api()

    api._get_items_in_value_batches(build_url, {'well': wells + wells[:10]}, 'well')

    sent = [value for call in recorder.calls for value in values_in(call.url, 'well')]
    assert sent == wells


def test_count_items_in_value_batches_sums_the_counts(monkeypatch: MonkeyPatch) -> None:
    wells = well_ids(201)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, None, headers={'X-Query-Count': '7'}),
        FakeResponse(200, None, headers={'X-Query-Count': '5'}),
        FakeResponse(200, None, headers={'X-Query-Count': '0'}),
    )
    api = make_offline_api()

    assert api._count_items_in_value_batches(build_url, {'well': wells}, 'well') == 12
    assert [call.method for call in recorder.calls] == ['HEAD'] * 3
    assert [len(values_in(call.url, 'well')) for call in recorder.calls] == [100, 100, 1]


def test_count_items_in_value_batches_uses_the_given_key(monkeypatch: MonkeyPatch) -> None:
    wells = well_ids(101)
    recorder = install_recording_transport(
        monkeypatch,
        FakeResponse(200, None, headers={'X-Query-Count': '1'}),
        FakeResponse(200, None, headers={'X-Query-Count': '2'}),
    )
    api = make_offline_api()

    assert api._count_items_in_value_batches(build_url, {'wellId': wells}, 'wellId') == 3
    assert [len(values_in(call.url, 'wellId')) for call in recorder.calls] == [100, 1]
