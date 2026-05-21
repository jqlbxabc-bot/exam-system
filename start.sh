#!/bin/bash
PORT=${PORT:-${SERVER_PORT:-${TENCENTCLOUD_RUN_PORT:-80}}}
echo "Starting on port $PORT"
exec gunicorn -b 0.0.0.0:$PORT -w 4 --timeout 120 wsgi:app
