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


def setup_logging(log_file: Path, log_level: str) -> None:
    """Setup logging configuration."""
    logger.add(
        sink=log_file,
        level=log_level,
    )


def version_callback(value: bool) -> None:
    """Return the program version."""
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def run_rss_alert(
    rss_url: str,
    settings: Settings,
    include: list[str] | None = None,
    include_any: bool = False,
    exclude: list[str] | None = None,
    exclude_any: bool = False,
    autoclean: bool = False,
    muted: bool = False,
) -> None:
    """Sync wrapper for CLI / cron usage."""
    from rss_alert.app import rss_alert

    try:
        asyncio.run(
            rss_alert(
                rss_url=rss_url,
                settings=settings,
                include=include,
                include_any=include_any,
                exclude=exclude,
                exclude_any=exclude_any,
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
    env_file: Annotated[
        Path | None,
        typer.Option("--env-file", "-e", help="Path to .env file. If not filled, rss-alert will try to detect one."),
    ] = None,
    include: Annotated[
        list[str] | None,
        typer.Option(
            "--include",
            "-i",
            help="Only alert on RSS feed items that include this text in the title. Can be used multiple times.",
        ),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            "--exclude",
            "-x",
            help="Only alert on RSS feed items that exclude this text in the title. Can be used multiple times.",
        ),
    ] = None,
    include_any: Annotated[
        bool,
        typer.Option(
            "--include-any",
            help="Match any include filter instead of requiring all filters",
        ),
    ] = False,
    exclude_any: Annotated[
        bool,
        typer.Option(
            "--exclude-any",
            help="Match any exclude filter instead of requiring all filters",
        ),
    ] = False,
    autoclean: Annotated[
        bool, typer.Option("--autoclean", help="Remove items from history if they are not in the feed anymore.")
    ] = False,
    muted: Annotated[bool, typer.Option("--muted", help="Don't send alerts, just log to screen.")] = False,
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
    settings = load_settings(env_file=env_file)
    setup_logging(log_file=settings.log_file, log_level=settings.log_level)

    for url in rss_urls:
        try:
            url_adapter.validate_python(url)
        except ValidationError:
            raise typer.BadParameter(f"'{url}' is not a valid URL")

        run_rss_alert(
            rss_url=url,
            settings=settings,
            include=include,
            include_any=include_any,
            exclude=exclude,
            exclude_any=exclude_any,
            autoclean=autoclean,
            muted=muted,
        )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
