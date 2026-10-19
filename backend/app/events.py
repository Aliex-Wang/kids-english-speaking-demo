import json
import threading
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_EVENT_PROPERTIES = {
    "theme",
    "difficulty",
    "success",
    "turns",
    "stars",
    "latency_ms",
    "error_type",
    "continued_after_help",
}


class EventLogger:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def log(
        self,
        name: str,
        properties: dict[str, str | int | bool] | None = None,
    ) -> None:
        properties = properties or {}
        forbidden = set(properties) - ALLOWED_EVENT_PROPERTIES
        if forbidden:
            raise ValueError(
                f"event properties not allowed: {sorted(forbidden)}"
            )
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": name,
            **properties,
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
