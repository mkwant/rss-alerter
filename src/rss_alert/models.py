from typing import Protocol


class Alerter(Protocol):
    async def send_alert(self, msg: str) -> None: ...


RSSItem = dict[str, str]
