# RSS Alert

A small CLI tool that monitors an RSS feed and sends a Telegram alert when new items match specified keywords.

## Installation

### Using `uv`

```bash
uv sync
```

Run:

```bash
rss-alert <rss-url>
```

### Using Docker

```bash
docker build -t rss-alert .
docker run --rm rss-alert <rss-url>
```

## Configuration

Rss-alert is configured via environment variables or a .env file.

```
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```
### Optional variables
```
LOG_LEVEL=INFO
LOG_FILE=logs/rss-alert.log
HISTORY_FILE=history/history.json
```

### Notes
- Paths can be relative or absolute.
- Relative paths are resolved from the current working directory.
- Environment variables override values defined in .env.

### Getting your Telegram chat ID

1. Open Telegram and search for bot @BotFather  
2. Create a bot:
    ```
    /start
    /newbot
    ```
    Copy the **bot token** → this is your `TELEGRAM_TOKEN`

3. Start a chat with your new bot and send any message (e.g. `hello`)

4. Open in your browser:

    `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`

5. Look for:
    ```json
    "chat": {
      "id": 123456789
    }
    ```
    That number is your TELEGRAM_CHAT_ID

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

### Example Cron Job

Run every 5 minutes:

```bash
*/5 * * * * rss-alert https://example.com/rss --filter <keyword1>
```
