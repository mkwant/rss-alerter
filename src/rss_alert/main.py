import asyncio
from typing import Annotated

import typer

from rss_alert.app import rss_alert

app = typer.Typer()

def run_rss_alert(rss_url: str) -> None:
    """Sync wrapper for CLI / cron usage."""
    asyncio.run(rss_alert(rss_url))

@app.command(no_args_is_help=True)
def alert(rss_urls: Annotated[list[str], typer.Argument(help="Send alerts for one or more RSS urls")]) -> None:
    for url in rss_urls:
        run_rss_alert(url)


# https://auctionrss.ceruliz.nl/montreuxjazzshop?search_term=bowie


def main() -> None:
    app()


if __name__ == "__main__":
    main()
