import asyncio
from typing import Annotated

import typer
from pydantic import HttpUrl, TypeAdapter, ValidationError

from rss_alert.app import rss_alert

app = typer.Typer(pretty_exceptions_enable=False)

url_adapter = TypeAdapter(HttpUrl)


def run_rss_alert(rss_url: str) -> None:
    """Sync wrapper for CLI / cron usage."""
    asyncio.run(rss_alert(rss_url))


@app.command(no_args_is_help=True)
def alert(rss_urls: Annotated[list[str], typer.Argument(help="Send alerts for one or more RSS urls")]) -> None:
    for url in rss_urls:
        try:
            url_adapter.validate_python(url)
        except ValidationError:
            raise typer.BadParameter(f"'{url}' is not a valid URL")

        run_rss_alert(url)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
