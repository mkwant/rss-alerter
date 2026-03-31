from dataclasses import dataclass
from pathlib import Path
from pyexpat import ExpatError

import httpx
import tenacity
import truststore
import xmltodict
from filelock import FileLock
from loguru import logger

from rss_alert.config import Settings
from rss_alert.history import load_history, save_history
from rss_alert.models import Alerter
from rss_alert.telegrambot import TelegramAlerter

truststore.inject_into_ssl()  # Use OS trust store


def escape_str(string: str) -> str:
    """Escape special characters for strings to be used in a markdown message."""
    string = string.replace("_", r"\_")
    string = string.replace("*", r"\*")
    return string


def format_message(item: dict[str, str]) -> str:
    """Helper to format the message"""
    try:
        return f"*{escape_str(item['title'])}*\n{escape_str(item['description'])}\n{escape_str(item['link'])}"
    except KeyError:
        return f"*{escape_str(item['title'])}*\n{escape_str(item['link'])}"


@tenacity.retry(stop=tenacity.stop_after_attempt(3))
async def fetch_rss(rss_url: str) -> list[dict[str, str]]:
    """Retrieves and parses the RSS feed"""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.get(rss_url)
        r.raise_for_status()

    try:
        rss_dict = xmltodict.parse(r.text)
    except ExpatError:
        logger.error(f"Failed to parse RSS feed at '{rss_url}', not a valid XML file.")
        return []

    try:
        items = rss_dict["rss"]["channel"]["item"]
    except KeyError:
        logger.error(f"RSS feed at '{rss_url}' has no items, not a valid XML file.")
        return []

    if isinstance(items, dict):
        items = [items]

    logger.info(f"Fetched RSS feed '{rss_url}' with {len(items)} items")
    return items


def get_guid(item: dict) -> str | None:
    guid = item.get("guid") or item.get("link")

    if isinstance(guid, dict):
        return guid.get("#text")

    return guid


@dataclass
class TitleFilter:
    include: list[str] | None
    include_any: bool
    exclude: list[str] | None
    exclude_any: bool

    def _include_separator(self) -> str:
        return "&" if self.include_any else "|"

    def _exclude_separator(self) -> str:
        return "&" if self.exclude_any else "|"

    def matches(self, title: str) -> bool:
        """Checks if the title matches the include/exclude patterns"""
        # Normalize
        self.include = [x.lower() for x in (self.include or [])]
        self.exclude = [x.lower() for x in (self.exclude or [])]
        title = title.lower()

        # Include filter
        if self.include:
            if self.include_any:
                include_match = any(x in title for x in self.include)
            else:
                include_match = all(x in title for x in self.include)

            if not include_match:
                return False

        # Exclude filter
        if self.exclude:
            if self.exclude_any:
                exclude_match = any(x in title for x in self.exclude)
            else:
                exclude_match = all(x in title for x in self.exclude)

            if exclude_match:
                return False

        return True

    def history_key(self) -> str:
        """Returns the history key"""
        include_part = self._include_separator().join(sorted(self.include)) if self.include else ""
        exclude_part = self._exclude_separator().join(sorted(self.exclude)) if self.exclude else ""
        return f"{include_part}/{exclude_part}"


async def process_feed(
    rss_url: str,
    alerter: Alerter,
    history_file: Path,
    title_filter: TitleFilter,
    autoclean: bool = False,
    muted: bool = False,
) -> None:
    """Processes the parsed RSS feed and sends an alert if new items are added"""

    # Read history file
    with FileLock(f"{history_file}.lock"):
        history = load_history(history_file=history_file)
    history_key = title_filter.history_key()
    feed_history = set(history.get(rss_url, {}).get(history_key, []))

    # Fetch RSS feed
    items = await fetch_rss(rss_url=rss_url)

    # Process RSS feed items
    new_items = False

    for item in items:
        guid = get_guid(item)

        title = item.get("title")
        if not title:
            logger.warning(f"No title found for {guid=}")
            continue

        if not guid:
            logger.warning(f"No guid found for {title=}")
            continue

        # Filtering
        if not title_filter.matches(title):
            logger.debug(f"Item filtered out ({guid=}, {title=})")
            continue

        # Check history
        if guid in feed_history:
            logger.debug(f"Old item: {guid=}, {title=}")
            continue

        # Send alert
        if not muted:
            logger.info(f"New item: {guid=}, {title=} - sending alert")
            await alerter.send_alert(format_message(item))
        else:
            logger.info(f"New item: {guid=}, {title=} - alert muted")

        feed_history.add(guid)
        new_items = True

    # Autoclean
    deleted_items = False
    if autoclean:
        new_items_guids = [get_guid(x) for x in items]

        for guid in feed_history.copy():
            if guid in new_items_guids:
                continue
            logger.info(f"Item found in history file but not in feed - deleting from history ({guid=})")
            feed_history.remove(guid)
            deleted_items = True

    # Save history
    if new_items or deleted_items:
        history.setdefault(rss_url, {})
        history[rss_url][history_key] = sorted(feed_history)
        save_history(history_file=history_file, history=history)


async def rss_alert(
    settings: Settings,
    rss_url: str,
    include: list[str] | None = None,
    include_any: bool = False,
    exclude: list[str] | None = None,
    exclude_any: bool = False,
    autoclean: bool = False,
    muted: bool = False,
) -> None:
    """Runs the RSS alert"""

    alerter = TelegramAlerter.from_settings(settings=settings)

    title_filter = TitleFilter(
        include=include,
        include_any=include_any,
        exclude=exclude,
        exclude_any=exclude_any,
    )

    await process_feed(
        alerter=alerter,
        rss_url=rss_url,
        title_filter=title_filter,
        autoclean=autoclean,
        muted=muted,
        history_file=settings.history_file,
    )
