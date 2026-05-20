#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runtime OCR improvements for photographed exam uploads."""

import builtins
import os
import re

_original_import = builtins.__import__


def _score_ocr_text(text):
    text = text or ''
    compact = re.sub(r'\s+', '', text)
    if not compact:
        return 0
    chinese = len(re.findall(r'[\u4e00-\u9fff]', compact))
    latin = len(re.findall(r'[A-Za-z0-9]', compact))
    exam_words = sum(8 for word in ['试卷', '考试', '选择题', '填空题', '解答题', '数学', '语文', '英语', '高三', '总分'] if word in text)
    return len(compact) + chinese * 2 + latin + exam_words


def _build_ocr_variants(image_path):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image).convert('RGB')

    width, height = image.size
    max_side = max(width, height)
    if max_side and max_side < 1800:
        scale = min(3.0, 1800 / max_side)
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

        tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        best_text = ''
        best_score = 0
        langs = ['chi_sim+eng', 'eng']
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


def _patch_exam_recognizer(module):
    recognizer_cls = getattr(module, 'ExamRecognizer', None)
    if not recognizer_cls or getattr(recognizer_cls, '_enhanced_ocr_patched', False):
        return

    original_extract = recognizer_cls.extract_text_from_image

    @staticmethod
    def extract_text_from_image(image_path):
        return _improved_extract_text_from_image(original_extract, image_path, recognizer_cls)

    recognizer_cls.extract_text_from_image = extract_text_from_image
    recognizer_cls._enhanced_ocr_patched = True
    print('Enhanced OCR preprocessing is enabled for photographed exams')


def _import_with_ocr_patch(name, globals=None, locals=None, fromlist=(), level=0):
    module = _original_import(name, globals, locals, fromlist, level)
    target = module
    if name == 'exam_recognizer':
        _patch_exam_recognizer(target)
    return module


builtins.__import__ = _import_with_ocr_patch
