"""The consumer's helpers, tested without a running Kafka broker."""

import json
from datetime import datetime, timezone

from streaming.consumer import batch_key, to_jsonl


def test_batch_files_land_in_the_stream_folder():
    key = batch_key(datetime(2026, 10, 1, 8, 30, 0, tzinfo=timezone.utc))
    assert key.startswith("landing/claim_events/stream/claim_events_20261001T083000")
    assert key.endswith(".jsonl")


def test_jsonl_has_one_event_per_line():
    events = [json.dumps({"event_id": str(i)}) for i in range(3)]
    lines = to_jsonl(events).decode("utf-8").splitlines()
    assert len(lines) == 3
    assert json.loads(lines[2])["event_id"] == "2"