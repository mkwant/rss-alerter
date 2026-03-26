from pathlib import Path

from dotenv import find_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_token: str
    telegram_chat_id: str
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
    )


def load_settings(env_file: Path | None = None) -> Settings:
    env_path = env_file or find_dotenv(usecwd=True) or None

    try:
        return Settings(_env_file=env_path)  # type: ignore
    except ValidationError as e:
        print("\n❌ Configuration error\n")

        if env_path is None:
            print("No .env file found.")
        else:
            print(f".env file used: {env_path}\n")
            print("Validation errors:")
            for err in e.errors():
                print(f" - {err['msg']}: {err['loc'][0]}")

        raise SystemExit(1)
