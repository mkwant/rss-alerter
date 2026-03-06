import httpx
import tenacity
import truststore
import xmltodict
from filelock import FileLock
from loguru import logger

from rss_alert.history import load_history, save_history
from rss_alert.models import Alerter
from rss_alert.telegrambot import TelegramAlerter

truststore.inject_into_ssl()


def format_message(item: dict[str, str]) -> str:
    """Helper to format the message"""
    return f"*{item['title']}*\n{item['description']}\n{item['link']}"


@tenacity.retry(stop=tenacity.stop_after_attempt(3))
async def parse_rss(rss_url: str) -> list[dict[str, str]]:
    """Retrieves and parses the RSS feed"""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(rss_url)
        r.raise_for_status()

    rss_dict = xmltodict.parse(r.text)
    items = rss_dict["rss"]["channel"]["item"]

    if isinstance(items, dict):
        items = [items]

    logger.info(f"Fetched RSS feed '{rss_url}' with {len(items)} items")
    return items


async def process_feed(rss_url: str, alerter: Alerter) -> None:
    """Processes the parsed RSS feed and sends an alert if new items are added"""
    with FileLock("history.json.lock"):
        history = load_history()
    feed_history = set(history.get(rss_url, []))  # convert to set for fast lookup

    items = await parse_rss(rss_url)

    new_items = False
    for item in items:
        guid = item.get("guid") or item.get("link")
        if not guid:
            logger.warning(f"No guid found for {item.get('title')}")
            continue
        if guid in feed_history:
            logger.info("Old item", guid=guid, title=item.get("title"))
            continue

        logger.info("New item", guid=guid, title=item.get("title"))
        await alerter.send_alert(format_message(item))
        feed_history.add(guid)
        new_items = True

    if new_items:
        # convert set back to list
        history[rss_url] = list(feed_history)
        save_history(history)


async def rss_alert(rss_url: str) -> None:
    """Runs the RSS alert"""
    alerter = TelegramAlerter.from_env()
    await process_feed(
        alerter=alerter,
        rss_url=rss_url,
    )
