#!/bin/bash
arguments=( "$@" )

cd /var/lib/rss-alert || exit
/bin/docker run --rm --quiet \
    --pull always \
    --env-file .env \
    -v "/var/log/rss-alert:/app/logs" \
    -v "$(pwd)/history:/app/history" \
    ghcr.io/mkwant/rss-alerter:latest uv run src/rss_alert/main.py "${arguments[@]}"
