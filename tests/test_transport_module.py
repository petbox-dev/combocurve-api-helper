"""The transport split out of `base.py`: the names `base` still re-exports, the batch chunk spec, and the
pure 207-body parser -- no live API."""

from typing import Any

import pytest

from combocurve_api_helper import _transport, base
from combocurve_api_helper._batch import ChunkSpec, _whole_chunk_failure, chunk_from_207_body

RE_EXPORTED_NAMES = [
    '_CALL_DEADLINE_SECONDS',
    '_CONNECTION_BACKOFF_SECONDS',
    '_GATEWAY_BACKOFF_SECONDS',
    '_MAX_CONNECTION_RETRIES',
    '_MAX_REQUEST_RETRIES',
    '_MAX_RETRY_AFTER_SECONDS',
    '_RATE_LIMIT_DEFAULT_PAUSE_SECONDS',
    '_READ_ONLY_METHODS',
    '_REQUEST_TIMEOUT_SECONDS',
    '_RETRYABLE_GATEWAY_STATUSES',
    '_CallDeadlinePassed',
    '_gateway_retry_allowed',
    '_is_read_only',
    '_next_page_url_on_request_origin',
    '_request_was_never_sent',
    '_retry_after_seconds',
    '_retry_delay_seconds',
    '_retry_fits_before_deadline',
    '_safe_to_send_again',
    '_send_request',
    '_timeout_within',
    'get_next_page_url',
]


@pytest.mark.parametrize('name', RE_EXPORTED_NAMES)
def test_base_re_exports_the_transport_name(name: str) -> None:
    assert getattr(base, name) is getattr(_transport, name)


SPEC = ChunkSpec(index=2, offset=10, records=[{'id': 'a'}, {'id': 'b'}, {'id': 'c'}])


def test_207_body_is_parsed() -> None:
    body = {
        'successCount': 2,
        'failedCount': 1,
        'results': [{'status': 'Created'}, 'not an object', {'status': 'Created'}, {'status': 'Error'}],
        'generalErrors': [{'name': 'E', 'message': 'm'}, 7],
    }

    chunk = chunk_from_207_body(SPEC, 207, body)

    assert (chunk.index, chunk.offset, chunk.count, chunk.http_status) == (2, 10, 3, 207)
    assert (chunk.success_count, chunk.failed_count) == (2, 1)
    assert chunk.results == [{'status': 'Created'}, {'status': 'Created'}, {'status': 'Error'}]
    assert chunk.general_errors == [{'name': 'E', 'message': 'm'}]
    assert not chunk.is_chunk_failure


@pytest.mark.parametrize('body', [None, [], 'text', {}, {'successCount': None, 'results': None}])
def test_body_that_is_not_an_envelope_reads_as_empty(body: Any) -> None:
    chunk = chunk_from_207_body(SPEC, 200, body)

    assert (chunk.success_count, chunk.failed_count, chunk.results, chunk.general_errors) == (0, 0, [], [])
    assert (chunk.count, chunk.http_status) == (3, 200)


def test_whole_chunk_failure_has_one_placeholder_per_record() -> None:
    chunk = _whole_chunk_failure(SPEC, http_status=502, error_message='boom', may_have_applied=True)

    assert (chunk.index, chunk.offset, chunk.count, chunk.failed_count) == (2, 10, 3, 3)
    assert chunk.is_chunk_failure and chunk.may_have_applied
    assert len(chunk.results) == 3
    assert chunk.results[0] == {
        'status': 'ChunkFailed',
        'code': 502,
        'errors': [{'name': 'ChunkFailed', 'message': 'boom'}],
        'mayHaveApplied': True,
    }
    assert chunk.results[0] is not chunk.results[1]
