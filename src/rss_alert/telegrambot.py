import os
from typing import Self

import dotenv
import telegram
from loguru import logger

dotenv.load_dotenv()


class TelegramAlerter:
    """Alerter for telegram chat"""

    def __init__(self, telegram_token: str | None, telegram_chat_id: str | None) -> None:
        if not telegram_token:
            error_msg = "Telegram token is required"
            logger.error(error_msg)
            raise ValueError(error_msg)
        if not telegram_chat_id:
            error_msg = "Telegram chat id is required"
            logger.error(error_msg)
            raise ValueError(error_msg)
        self.telegram_token: str = telegram_token
        self.telegram_chat_id: str = telegram_chat_id
        self.bot = telegram.Bot(token=self.telegram_token)

    @classmethod
    def from_env(cls) -> Self:
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )

    async def send_alert(self, msg: str) -> None:
        """Send a message to the telegram chat"""
        await self.bot.send_message(
            chat_id=self.telegram_chat_id,
            text=msg,
            parse_mode="markdown",
        )
