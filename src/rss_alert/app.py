from pathlib import Path
from pyexpat import ExpatError

import httpx
import tenacity
import xmltodict
from filelock import FileLock
from loguru import logger

from rss_alert.history import load_history, save_history
from rss_alert.models import Alerter
from rss_alert.telegrambot import TelegramAlerter

logger.add(sink=Path("logs/rss-alert.log"), level="INFO")


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
    async with httpx.AsyncClient(timeout=30) as client:
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


async def process_feed(rss_url: str, alerter: Alerter, title_filter: str = "") -> None:
    """Processes the parsed RSS feed and sends an alert if new items are added"""
    title_filter = title_filter.lower()
    with FileLock("history.json.lock"):
        history = load_history()
    # Convert to set for faster lookups
    feed_history = set(history.get(rss_url, {}).get(title_filter, []))

    items = await fetch_rss(rss_url)

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

        if title_filter not in title.lower():
            logger.debug(f"Item doesn't match filter '{title_filter}', skipped: {guid=}, {title=}")
            continue

        if guid in feed_history:
            logger.debug(f"Old item: {guid=}, {title=}")
            continue

        logger.info(f"New item: {guid=}, {title=} - sending alert")
        await alerter.send_alert(format_message(item))
        feed_history.add(guid)
        new_items = True

    if new_items:
        # convert set back to list
        history.setdefault(rss_url, {})
        history[rss_url][title_filter] = list(feed_history)
        save_history(history)


async def rss_alert(rss_url: str, title_filter: str = "") -> None:
    """Runs the RSS alert"""
    alerter = TelegramAlerter.from_env()
    await process_feed(
        alerter=alerter,
        rss_url=rss_url,
        title_filter=title_filter,
    )
