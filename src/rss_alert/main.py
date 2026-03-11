import asyncio
from typing import Annotated

import typer
from pydantic import HttpUrl, TypeAdapter, ValidationError

from rss_alert.app import rss_alert

app = typer.Typer(pretty_exceptions_enable=False, add_completion=False, no_args_is_help=True)
url_adapter = TypeAdapter(HttpUrl)


def run_rss_alert(rss_url: str, title_filters: list[str] | None) -> None:
    """Sync wrapper for CLI / cron usage."""
    asyncio.run(rss_alert(rss_url=rss_url, title_filters=title_filters))


@app.command(help="RSS Alerter, send Telegram notifications for new RSS entries.", no_args_is_help=True)
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
) -> None:
    for url in rss_urls:
        try:
            url_adapter.validate_python(url)
        except ValidationError:
            raise typer.BadParameter(f"'{url}' is not a valid URL")

        run_rss_alert(rss_url=url, title_filters=title_filters)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
