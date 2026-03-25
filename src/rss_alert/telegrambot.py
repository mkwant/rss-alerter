from typing import Self

from loguru import logger


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

    @classmethod
    def from_settings(cls, settings) -> Self:
        return cls(
            telegram_token=settings.telegram_token,
            telegram_chat_id=settings.telegram_chat_id,
        )

    async def send_alert(self, msg: str) -> None:
        """Send a message to the telegram chat"""
        import telegram

        bot = telegram.Bot(token=self.telegram_token)
        try:
            await bot.send_message(
                chat_id=self.telegram_chat_id,
                text=msg,
                parse_mode="markdown",
            )
        except telegram.error.TelegramError as e:
            logger.error(f"Error sending telegram message {msg=}: {e}")
