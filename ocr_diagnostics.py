#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OCR diagnostics endpoint for cloud deployments."""

import os
import shutil
import subprocess


def register_ocr_diagnostics(app):
    @app.route('/admin/ocr-diagnostics')
    def ocr_diagnostics():
        info = {
            'python_pytesseract': False,
            'tesseract_cmd': shutil.which('tesseract'),
            'tesseract_version': None,
            'tesseract_languages': [],
            'tessdata_prefix': os.environ.get('TESSDATA_PREFIX', ''),
            'status': 'unknown',
            'error': None,
        }

        try:
            import pytesseract
            info['python_pytesseract'] = True

            try:
                info['tesseract_version'] = str(pytesseract.get_tesseract_version())
            except Exception as exc:
                info['error'] = f'tesseract version check failed: {exc}'

            try:
                info['tesseract_languages'] = pytesseract.get_languages(config='')
            except Exception as exc:
                info['error'] = f'tesseract language check failed: {exc}'
        except Exception as exc:
            info['error'] = f'pytesseract import failed: {exc}'

        if info['tesseract_cmd']:
            try:
                output = subprocess.run(
                    ['tesseract', '--list-langs'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                info['tesseract_list_langs_output'] = output.stdout + output.stderr
            except Exception as exc:
                info['tesseract_list_langs_output'] = f'failed: {exc}'

        has_required = (
            info['python_pytesseract']
            and info['tesseract_cmd']
            and 'chi_sim' in info['tesseract_languages']
        )
        info['status'] = 'ok' if has_required else 'not_ready'
        return info
