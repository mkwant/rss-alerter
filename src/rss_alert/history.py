import json
from pathlib import Path

HISTORY_FILE = Path("history/history.json")


def load_history() -> dict[str, list[str]]:
    """Return history as {feed_url: [guid1, guid2, ...]}"""
    if not HISTORY_FILE.exists():
        return {}
    return json.loads(HISTORY_FILE.read_text())


def save_history(history: dict[str, list[str]]) -> None:
    HISTORY_FILE.write_text(json.dumps(obj=history, indent=4))
