import asyncio
from pathlib import Path
from typing import Annotated

import httpx
import tenacity
import typer
from loguru import logger
from pydantic import HttpUrl, TypeAdapter, ValidationError

from rss_alert import __version__
from rss_alert.config import Settings, load_settings

app = typer.Typer(pretty_exceptions_enable=False, add_completion=False, no_args_is_help=True)
url_adapter = TypeAdapter(HttpUrl)


def setup_logging(log_level: str) -> None:
    """Setup logging configuration."""
    Path("logs").mkdir(exist_ok=True)

    logger.add(
        sink=Path("logs/rss-alert.log"),
        level=log_level,
    )


def version_callback(value: bool) -> None:
    """Return the program version."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def run_rss_alert(
    rss_url: str,
    title_filters: list[str] | None,
    settings: Settings,
    match_any: bool = False,
    autoclean: bool = False,
    muted: bool = False,
) -> None:
    """Sync wrapper for CLI / cron usage."""
    from rss_alert.app import rss_alert

    try:
        asyncio.run(
            rss_alert(
                rss_url=rss_url,
                title_filters=title_filters,
                settings=settings,
                match_any=match_any,
                autoclean=autoclean,
                muted=muted,
            )
        )
    except tenacity.RetryError as e:
        cause = e.last_attempt.exception()

        if isinstance(cause, httpx.HTTPStatusError):
            logger.error(f"Failed to fetch RSS feed: HTTP error {cause.response.status_code} for {cause.request.url}")
        elif isinstance(cause, httpx.RequestError):
            logger.error(f"Network error while fetching RSS feed: {cause}")
        else:
            logger.error(f"RSS fetch failed after retries: {cause}")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")


@app.command(help="RSS Alert, send Telegram notifications for new RSS entries.", no_args_is_help=True)
def alert(
    rss_urls: Annotated[list[str], typer.Argument(help="Send alerts for one or more RSS urls")],
    title_filters: Annotated[
        list[str] | None,
        typer.Option(
            "--filter",
            "-f",
            help="Only alert on RSS feed items with this text in the title. Can be used multiple times.",
        ),
    ] = None,
    env_file: Annotated[
        str | None,
        typer.Option("--env-file", "-e", help="Path to .env file. If not filled, script will try to detect one."),
    ] = None,
    match_any: Annotated[
        bool,
        typer.Option(
            "--any/--all",
            help="Match any filter instead of requiring all filters",
        ),
    ] = False,
    autoclean: Annotated[
        bool, typer.Option(help="Remove items from history if they are not in the feed anymore.")
    ] = False,
    muted: Annotated[bool, typer.Option("--muted/--alert", help="Don't send alerts, just log to screen.")] = False,
    _show_version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    settings = load_settings(env_file)
    setup_logging(settings.log_level)

    for url in rss_urls:
        try:
            url_adapter.validate_python(url)
        except ValidationError:
            raise typer.BadParameter(f"'{url}' is not a valid URL")

        run_rss_alert(
            rss_url=url,
            title_filters=title_filters,
            settings=settings,
            match_any=match_any,
            autoclean=autoclean,
            muted=muted,
        )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
