from pathlib import Path
from pyexpat import ExpatError

import httpx
import tenacity
import truststore
import xmltodict
from filelock import FileLock
from loguru import logger

from rss_alert.config import Settings
from rss_alert.history import create_history_key, load_history, save_history
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


async def process_feed(
    rss_url: str,
    alerter: Alerter,
    history_file: Path,
    title_filters: list[str] | None = None,
    match_any: bool = False,
    autoclean: bool = False,
    muted: bool = False,
) -> None:
    """Processes the parsed RSS feed and sends an alert if new items are added"""
    if not title_filters:
        title_filters = [""]
    title_filters = [x.lower() for x in title_filters]

    if match_any:
        separator = "&"
    else:
        separator = "|"

    with FileLock(f"{history_file}.lock"):
        history = load_history(history_file=history_file)
    # Convert to set for faster lookups
    feed_history = set(history.get(rss_url, {}).get(create_history_key(title_filters, separator), []))

    items = await fetch_rss(rss_url=rss_url)

    new_items = False
    for item in items:
        guid = item.get("guid") or item.get("link")

        # If guid has a isPermaLink flag, use just the guid
        if isinstance(guid, dict):
            guid = guid.get("#text")

        title = item.get("title")
        if not title:
            logger.warning(f"No title found for {guid=}")
            continue

        if not guid:
            logger.warning(f"No guid found for {title=}")
            continue

        if match_any:
            matches = any(x in title.lower() for x in title_filters)
        else:
            matches = all(x in title.lower() for x in title_filters)

        if not matches:
            logger.debug(f"Item doesn't match filter {title_filters}, skipped. ({guid=}, {title=})")
            continue

        if guid in feed_history:
            logger.debug(f"Old item: {guid=}, {title=}")
            continue

        if not muted:
            logger.info(f"New item: {guid=}, {title=} - sending alert")
            await alerter.send_alert(format_message(item))
        else:
            logger.info(f"New item: {guid=}, {title=} - alert muted")
        feed_history.add(guid)
        new_items = True

    deleted_items = False
    if autoclean:
        new_items_guids = [x.get("guid") for x in items]
        for guid in feed_history.copy():
            if guid in new_items_guids:
                continue
            logger.info(f"Item found in history file but not in feed - deleting from history ({guid=})")
            feed_history.remove(guid)
            deleted_items = True

    if new_items or deleted_items:
        # convert set back to list
        history.setdefault(rss_url, {})
        history_key = create_history_key(title_filters=title_filters, separator=separator)
        history[rss_url][history_key] = sorted(list(feed_history))
        save_history(history_file=history_file, history=history)


async def rss_alert(
    settings: Settings,
    rss_url: str,
    title_filters: list[str] | None = None,
    match_any: bool = False,
    autoclean: bool = False,
    muted: bool = False,
) -> None:
    """Runs the RSS alert"""
    alerter = TelegramAlerter.from_settings(settings=settings)
    await process_feed(
        alerter=alerter,
        rss_url=rss_url,
        title_filters=title_filters,
        match_any=match_any,
        autoclean=autoclean,
        muted=muted,
        history_file=settings.history_file,
    )
