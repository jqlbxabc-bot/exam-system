#!/usr/bin/env python3
"""Container startup entrypoint."""
import os
import sys
from gunicorn.app.wsgiapp import run

port = (
    os.environ.get('PORT')
    or os.environ.get('SERVER_PORT')
    or os.environ.get('TENCENTCLOUD_RUN_PORT')
    or '80'
)
print(f"Starting gunicorn on port {port}")

sys.argv = [
    'gunicorn',
    '-b', f'0.0.0.0:{port}',
    '-w', '4',
    '--timeout', '120',
    'wsgi:app'
]

run()
