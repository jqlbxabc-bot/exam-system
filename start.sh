#!/bin/bash
PORT=${PORT:-5001}
echo "Starting on port $PORT"
exec gunicorn -b 0.0.0.0:$PORT -w 4 --timeout 120 wsgi:app
