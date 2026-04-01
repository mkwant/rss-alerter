from typing import Protocol


class Alerter(Protocol):
    async def send_alert(self, msg: str) -> None: ...


class ItemFilter(Protocol):
    def matches(self, feed_item: RSSItem) -> bool: ...

    def history_key(self) -> str: ...


RSSItem = dict[str, str]
