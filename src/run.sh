#!/bin/bash
arguments=( "$@" )

cd /var/lib/rss-alert || exit
/bin/docker run -it --rm --quiet \
    --pull always \
    --env-file .env \
    -v "$(pwd)/history:/app/history" \
    ghcr.io/mkwant/rss-alerter:latest uv run src/rss_alert/main.py "${arguments[@]}"
