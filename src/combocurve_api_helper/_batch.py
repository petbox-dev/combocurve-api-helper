"""Structured, parallel batch-write support.

This intentionally departs from the package's usual `ItemList` return. Batch
writes to ComboCurve reply with **207 Multi-Status**
(`{successCount, failedCount, results[], generalErrors}`) where `results[i]`
corresponds positionally to the request payload's item `i`. Flattening that to
an `ItemList` (as `_post_items` / `_put_items` do) discards which records were
rejected, so a no-exception write looks like a full success even when records
failed. `BatchWriteResult` preserves the envelope so callers can detect and
report partial failures.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import Item, ItemList


@dataclass(frozen=True)
class ChunkSpec:
    """One chunk of a batched write, before it is sent."""

    index: int  # 0-based chunk number (order the chunks were split from the payload)
    offset: int  # index of this chunk's first record in the full payload
    records: ItemList  # the chunk's records, sent as the request body


@dataclass
class BatchChunk:
    """One chunk of a batched write and its parsed 207 result."""

    index: int  # 0-based chunk number (order the chunks were split from the payload)
    offset: int  # index of this chunk's first record in the full payload
    count: int  # number of records in this chunk
    http_status: int  # 0 when no response was received (the connection failed)
    success_count: int = 0
    failed_count: int = 0
    results: ItemList = field(default_factory=list)  # 207 results[], aligned to this chunk's payload
    general_errors: ItemList = field(default_factory=list)
    error_message: str = ''  # set on whole-chunk failure (4xx/5xx, exhausted 429 retries, lost connection)
    # True when the chunk failed but the server may still have applied it: a write that got a
    # gateway status (502/503/504) or lost its connection after it was sent. Do not send such a
    # chunk again without first checking what the server holds; a second send can write it twice.
    may_have_applied: bool = False

    @property
    def is_chunk_failure(self) -> bool:
        """True when the whole chunk failed (vs. individual records in `results`)."""
        return bool(self.error_message)


@dataclass
class BatchWriteResult:
    """Aggregated result of a batched write across all chunks.

    `results` is stitched back into the original payload order, so
    `results[i]` corresponds to the input `data[i]`.
    """

    success_count: int
    failed_count: int
    results: ItemList  # per-record, in the original payload order
    general_errors: ItemList
    chunks: list[BatchChunk]

    @property
    def ok(self) -> bool:
        """True iff every record succeeded and no chunk failed wholesale."""
        return self.failed_count == 0 and not any(c.is_chunk_failure for c in self.chunks)


@dataclass
class _RateLimitState:
    """Shared 429 coordination across batch-write worker threads: a 429 in any
    worker pauses every worker until the quota window resets."""

    pause_seconds: float
    lock: threading.Lock = field(default_factory=threading.Lock)
    resume_at: float = 0.0

    def wait_if_limited(self) -> None:
        """Block until any active rate-limit pause has elapsed."""
        with self.lock:
            deadline = self.resume_at
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)

    def set_limited(self, retry_after_seconds: float | None = None) -> None:
        """Record a 429 hit — all workers pause for `retry_after_seconds` (the response's
        `Retry-After`) when given, else for `pause_seconds`."""
        pause = self.pause_seconds if retry_after_seconds is None else retry_after_seconds
        with self.lock:
            self.resume_at = max(self.resume_at, time.monotonic() + pause)


def _whole_chunk_failure(
    chunk_spec: ChunkSpec, *, http_status: int, error_message: str, may_have_applied: bool
) -> BatchChunk:
    """A chunk that failed as a whole, with one placeholder result per record.

    The placeholders keep `BatchWriteResult.results[i]` aligned with `data[i]` after the chunks are
    stitched together; without them every later chunk's results shift left, and a caller that picks
    records to resend by position picks the wrong ones. Each has the shape of a 207 error element.
    """
    count = len(chunk_spec.records)
    placeholder: Item = {
        'status': 'ChunkFailed',
        'code': http_status,
        'errors': [{'name': 'ChunkFailed', 'message': error_message}],
        'mayHaveApplied': may_have_applied,
    }
    return BatchChunk(
        index=chunk_spec.index,
        offset=chunk_spec.offset,
        count=count,
        http_status=http_status,
        failed_count=count,
        results=[dict(placeholder) for _ in range(count)],
        error_message=error_message,
        may_have_applied=may_have_applied,
    )


def chunk_from_207_body(chunk_spec: ChunkSpec, http_status: int, body: object) -> BatchChunk:
    """The `BatchChunk` of a chunk whose request succeeded, from its decoded 207 body.

    `body` is the decoded JSON, or None when the body was not JSON. A body that is not a JSON object
    reads as an empty envelope (zero counts, no results); `results` and `generalErrors` keep only their
    object elements.
    """
    envelope: dict[str, Any] = body if isinstance(body, dict) else {}
    results_raw = envelope.get('results') or []
    general_raw = envelope.get('generalErrors') or []
    return BatchChunk(
        index=chunk_spec.index,
        offset=chunk_spec.offset,
        count=len(chunk_spec.records),
        http_status=http_status,
        success_count=int(envelope.get('successCount', 0) or 0),
        failed_count=int(envelope.get('failedCount', 0) or 0),
        results=[result for result in results_raw if isinstance(result, dict)],
        general_errors=[error for error in general_raw if isinstance(error, dict)],
    )
