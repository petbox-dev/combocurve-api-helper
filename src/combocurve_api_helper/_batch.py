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
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .base import ItemList


@dataclass
class BatchChunk:
    """One chunk of a batched write and its parsed 207 result."""

    index: int  # 0-based chunk number (order the chunks were split from the payload)
    offset: int  # index of this chunk's first record in the full payload
    count: int  # number of records in this chunk
    http_status: int
    success_count: int = 0
    failed_count: int = 0
    results: ItemList = field(default_factory=list)  # 207 results[], aligned to this chunk's payload
    general_errors: ItemList = field(default_factory=list)
    error_message: str = ''  # set on whole-chunk failure (4xx/5xx or exhausted 429 retries)

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
    chunks: List[BatchChunk]

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

    def set_limited(self) -> None:
        """Record a 429 hit — all workers pause until `pause_seconds` from now."""
        with self.lock:
            self.resume_at = max(self.resume_at, time.monotonic() + self.pause_seconds)
