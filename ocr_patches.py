#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runtime OCR improvements for photographed exam uploads."""

import builtins
import os
import re
import shutil

_original_import = builtins.__import__

VISION_PROVIDER_MODELS = {
    'openai': ['gpt-4o', 'gpt-4.1', 'gpt-5', 'vision'],
    'qwen': ['vl', 'qvq', 'vision'],
    'zhipu': ['glm-4v', 'vision'],
    'claude': ['claude-3', 'claude-4'],
}

TEXT_ONLY_PROVIDERS = {'deepseek', 'moonshot', 'local'}


def _score_ocr_text(text):
    text = text or ''
    compact = re.sub(r'\s+', '', text)
    if not compact:
        return 0
    chinese = len(re.findall(r'[\u4e00-\u9fff]', compact))
    latin = len(re.findall(r'[A-Za-z0-9]', compact))
    exam_words = sum(8 for word in ['试卷', '考试', '选择题', '填空题', '解答题', '数学', '语文', '英语', '高三', '总分'] if word in text)
    return len(compact) + chinese * 2 + latin + exam_words


def _supports_vision(analyzer):
    provider = (getattr(analyzer, 'provider', '') or '').lower()
    model = (getattr(analyzer, 'model', '') or '').lower()
    if provider in TEXT_ONLY_PROVIDERS:
        return False
    model_keywords = VISION_PROVIDER_MODELS.get(provider, [])
    if not model_keywords:
        return False
    return any(keyword in model for keyword in model_keywords)


def _configure_tesseract(pytesseract):
    windows_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    linux_cmd = shutil.which('tesseract')
    if os.path.exists(windows_cmd):
        pytesseract.pytesseract.tesseract_cmd = windows_cmd
    elif linux_cmd:
        pytesseract.pytesseract.tesseract_cmd = linux_cmd

    if not os.environ.get('TESSDATA_PREFIX'):
        for path in [
            '/usr/share/tesseract-ocr/5/tessdata',
            '/usr/share/tesseract-ocr/4.00/tessdata',
            '/usr/share/tesseract-ocr/tessdata',
            '/usr/share/tessdata',
        ]:
            if os.path.exists(path):
                os.environ['TESSDATA_PREFIX'] = path
                break


def _available_ocr_languages(pytesseract):
    try:
        return set(pytesseract.get_languages(config=''))
    except Exception as exc:
        print(f'Unable to list OCR languages: {exc}')
        return set()


def _build_ocr_variants(image_path):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image).convert('RGB')

    width, height = image.size
    max_side = max(width, height)
    if max_side and max_side < 2200:
        scale = min(3.0, 2200 / max_side)
        image = image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    sharp = gray.filter(ImageFilter.SHARPEN)
    high_contrast = ImageEnhance.Contrast(sharp).enhance(1.8)
    threshold = high_contrast.point(lambda p: 255 if p > 170 else 0)

    return [
        ('original', image),
        ('gray', gray),
        ('sharp', sharp),
        ('contrast', high_contrast),
        ('threshold', threshold),
    ]


def _improved_extract_text_from_image(original_method, image_path, recognizer_cls):
    try:
        import pytesseract

        _configure_tesseract(pytesseract)
        languages = _available_ocr_languages(pytesseract)
        if languages:
            print(f'OCR languages available: {sorted(languages)}')
        else:
            print('OCR languages unavailable; tesseract may not be installed correctly')

        best_text = ''
        best_score = 0
        langs = []
        if 'chi_sim' in languages and 'eng' in languages:
            langs.append('chi_sim+eng')
        if 'chi_sim' in languages:
            langs.append('chi_sim')
        if 'eng' in languages:
            langs.append('eng')
        if not langs:
            langs = ['chi_sim+eng', 'chi_sim', 'eng']

        configs = [
            '--oem 3 --psm 6',
            '--oem 3 --psm 3',
            '--oem 3 --psm 11',
        ]

        for variant_name, image in _build_ocr_variants(image_path):
            for lang in langs:
                for config in configs:
                    try:
                        text = pytesseract.image_to_string(image, lang=lang, config=config)
                    except Exception as exc:
                        print(f'OCR variant failed: {variant_name}, {lang}, {config}: {exc}')
                        continue
                    score = _score_ocr_text(text)
                    if score > best_score:
                        best_text = text
                        best_score = score

        if best_text and best_score >= 20:
            print(f'Enhanced OCR success, score={best_score}, length={len(best_text)}')
            return best_text
        print(f'Enhanced OCR returned weak text, score={best_score}, length={len(best_text)}')
    except ImportError:
        print('pytesseract is not installed')
    except Exception as exc:
        print(f'Enhanced OCR failed: {exc}')

    try:
        baidu_text = recognizer_cls._baidu_ocr(image_path)
        if baidu_text:
            return baidu_text
    except Exception as exc:
        print(f'Baidu OCR fallback failed: {exc}')

    try:
        return original_method(image_path)
    except Exception as exc:
        print(f'Original OCR fallback failed: {exc}')
        return ''


def _analyze_image_with_capability_check(original_method, recognizer_cls, image_path):
    try:
        from ai_analyzer import get_analyzer
        analyzer = get_analyzer()
    except Exception as exc:
        print(f'Unable to read model capability, using OCR fallback: {exc}')
        analyzer = None

    if analyzer and _supports_vision(analyzer):
        print(f'Model supports image recognition: provider={analyzer.provider}, model={analyzer.model}')
        return original_method(image_path)

    if analyzer:
        print(f'Model does not support image recognition, using OCR first: provider={analyzer.provider}, model={analyzer.model}')
    text = recognizer_cls.extract_text_from_image(image_path)
    if text and len(text.strip()) > 10:
        return recognizer_cls.analyze_with_ai(text, [image_path])

    print('OCR text is too short for AI analysis; image recognition skipped for text-only model')
    return None


def _patch_exam_recognizer(module):
    recognizer_cls = getattr(module, 'ExamRecognizer', None)
    if not recognizer_cls or getattr(recognizer_cls, '_enhanced_ocr_patched', False):
        return

    original_extract = recognizer_cls.extract_text_from_image
    original_analyze_image = recognizer_cls.analyze_image_with_ai

    @staticmethod
    def extract_text_from_image(image_path):
        return _improved_extract_text_from_image(original_extract, image_path, recognizer_cls)

    @staticmethod
    def analyze_image_with_ai(image_path):
        return _analyze_image_with_capability_check(original_analyze_image, recognizer_cls, image_path)

    recognizer_cls.extract_text_from_image = extract_text_from_image
    recognizer_cls.analyze_image_with_ai = analyze_image_with_ai
    recognizer_cls.model_supports_vision = staticmethod(lambda analyzer: _supports_vision(analyzer))
    recognizer_cls._enhanced_ocr_patched = True
    print('Enhanced OCR and model capability routing are enabled for photographed exams')


def _import_with_ocr_patch(name, globals=None, locals=None, fromlist=(), level=0):
    module = _original_import(name, globals, locals, fromlist, level)
    if name == 'exam_recognizer':
        _patch_exam_recognizer(module)
    return module


builtins.__import__ = _import_with_ocr_patch
