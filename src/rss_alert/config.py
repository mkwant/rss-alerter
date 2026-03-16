import sys

from dotenv import find_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = find_dotenv(usecwd=True) or None


class Settings(BaseSettings):
    telegram_token: str
    telegram_chat_id: str
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


try:
    settings = Settings()  # noqa # ty: ignore[missing-argument]
except ValidationError as e:
    print("\n❌ Configuration error\n")

    if ENV_FILE is None:
        print("No .env file found.")
    else:
        print(f".env file found at: {ENV_FILE}\n")
        print("Validation errors:")
        for err in e.errors():
            print(f" - {err['msg']}: {err['loc'][0]}")

    sys.exit(1)
