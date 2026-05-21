#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI diagnostics endpoint for cloud deployments."""

import os


def _mask(value):
    if not value:
        return ''
    value = str(value)
    if len(value) <= 8:
        return '*' * len(value)
    return value[:4] + '*' * (len(value) - 8) + value[-4:]


def register_ai_diagnostics(app):
    @app.route('/admin/ai-diagnostics')
    def ai_diagnostics():
        from ai_analyzer import get_analyzer

        analyzer = get_analyzer()
        provider = getattr(analyzer, 'provider', '')
        model = getattr(analyzer, 'model', '')
        base_url = getattr(analyzer, 'base_url', '')
        api_key = getattr(analyzer, 'api_key', '')

        info = {
            'provider': provider,
            'model': model,
            'base_url': base_url,
            'api_key_configured': bool(api_key),
            'api_key_masked': _mask(api_key),
            'env': {
                'AI_PROVIDER': os.environ.get('AI_PROVIDER', ''),
                'AI_MODEL': os.environ.get('AI_MODEL', ''),
                'AI_BASE_URL': os.environ.get('AI_BASE_URL', ''),
                'AI_API_KEY_configured': bool(os.environ.get('AI_API_KEY')),
                'DEEPSEEK_API_KEY_configured': bool(os.environ.get('DEEPSEEK_API_KEY')),
                'DASHSCOPE_API_KEY_configured': bool(os.environ.get('DASHSCOPE_API_KEY')),
                'OPENAI_API_KEY_configured': bool(os.environ.get('OPENAI_API_KEY')),
            },
            'status': 'configured' if api_key or provider == 'local' else 'missing_api_key',
        }

        try:
            result = analyzer.chat('只回复 JSON: {"ok": true}')
            info['test_response_preview'] = str(result)[:500]
            info['test_status'] = 'ok' if result and not str(result).startswith('错误') else 'failed'
        except Exception as exc:
            info['test_status'] = 'failed'
            info['test_error'] = str(exc)

        return info
