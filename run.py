#!/usr/bin/env python3
"""Railway 启动入口 - 用Python读取PORT，避免shell展开问题"""
import os
import sys
from gunicorn.app.wsgiapp import run

port = os.environ.get('PORT', '5001')
print(f"Starting gunicorn on port {port}")

sys.argv = [
    'gunicorn',
    '-b', f'0.0.0.0:{port}',
    '-w', '4',
    '--timeout', '120',
    'wsgi:app'
]

run()
