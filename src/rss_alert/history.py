import json
from pathlib import Path


def load_history(history_file: Path) -> dict[str, dict[str, list[str]]]:
    """Return history as {feed_url: [guid1, guid2, ...]}"""
    if not history_file.exists():
        return {}
    return json.loads(history_file.read_text())


def save_history(history_file: Path, history: dict[str, dict[str, list[str]]]) -> None:
    """Save history as {feed_url: [guid1, guid2, ...]}"""
    history_file.write_text(json.dumps(obj=history, indent=4, sort_keys=True))
