# RSS Alert

A small CLI tool that monitors an RSS feed and sends a Telegram alert when new items match specified keywords.

---

## Installation

### Using `uv`

```bash
uv sync
```

Run:

```bash
rss-alert <rss-url>
```

---

### Using Docker

```bash
docker build -t rss-alert .
docker run --rm rss-alert <rss-url>
```

---

## Usage

```bash
rss-alert <rss-url> --filter <keyword>
```

Multiple filters:

```bash
rss-alert <rss-url> --filter <keyword1> --filter <keyword2>
```

By default **all filters must match**.
Use `--match-any` to trigger when **any filter matches**:

```bash
rss-alert <rss-url> --filter <keyword1> --filter <keyword2> --match-any
```

---

## Telegram Alerts

Set environment variables:

```
TELEGRAM_TOKEN=<bot token>
TELEGRAM_CHAT_ID=<chat id>
```

Example:

```bash
export TELEGRAM_TOKEN=123456:ABCDEF
export TELEGRAM_CHAT_ID=123456789
```

---

## Example Cron Job

Run every 5 minutes:

```bash
*/5 * * * * rss-alert https://example.com/rss --filter bowie
```
