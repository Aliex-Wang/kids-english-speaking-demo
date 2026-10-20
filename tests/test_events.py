import json

import pytest

from app.events import EventLogger


def test_logs_allowlisted_event(tmp_path):
    path = tmp_path / "logs" / "events.jsonl"
    logger = EventLogger(path)
    logger.log(
        "turn_completed",
        {"theme": "family", "difficulty": "explorer", "stars": 2},
    )
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["event"] == "turn_completed"
    assert record["theme"] == "family"
    assert record["difficulty"] == "explorer"
    assert record["stars"] == 2
    assert "ts" in record


@pytest.mark.parametrize("key", ["text", "audio", "transcript", "child_text"])
def test_rejects_private_content_keys(tmp_path, key):
    logger = EventLogger(tmp_path / "events.jsonl")
    with pytest.raises(ValueError):
        logger.log("technical_error", {key: "private content"})


def test_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "events.jsonl"
    EventLogger(path).log("practice_started", {"difficulty": "sprout"})
    assert path.exists()
