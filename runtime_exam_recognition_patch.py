#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Patch uploaded exam recognition to extract question lists reliably."""

import builtins
import json
import re

_original_import = builtins.__import__


def _json_from_text(text):
    text = (text or '').strip()
    if not text:
        return None
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
    if text.endswith('```'):
        text = text[:-3]
    if text.lower().startswith('json'):
        text = text[4:]

    candidates = [text]
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            return json.loads(candidate.strip(), strict=False)
        except Exception:
            pass
    return None


def _normalize_question(raw, index):
    if not isinstance(raw, dict):
        return None
    number = raw.get('question_number') or raw.get('number') or raw.get('题号') or index
    try:
        number = int(number)
    except Exception:
        number = index

    content = raw.get('content') or raw.get('question') or raw.get('题目') or ''
    options = raw.get('options') or raw.get('选项') or ''
    if isinstance(options, (list, tuple)):
        options = '\n'.join(str(item) for item in options)
    if options and options not in content:
        content = f"{content}\n{options}"

    content = str(content or '').strip()
    if len(content) < 5:
        return None

    return {
        'number': number,
        'type': raw.get('question_type') or raw.get('type') or raw.get('题型') or '解答题',
        'content': content[:2000],
        'answer': raw.get('correct_answer') or raw.get('answer') or raw.get('答案'),
        'score': raw.get('score') or raw.get('分值') or 0,
    }


def _patch_exam_recognizer(module):
    recognizer = getattr(module, 'ExamRecognizer', None)
    if not recognizer or getattr(recognizer, '_question_ai_patched', False):
        return

    original_recognize_exam = recognizer.recognize_exam

    @staticmethod
    def analyze_with_ai(text, file_paths=None):
        from ai_analyzer import get_analyzer

        prompt = f"""请识别下面的高中试卷内容，并只返回严格 JSON。

试卷内容：
{text[:9000]}

JSON 格式如下：
{{
  "title": "试卷标题",
  "subject": "语文/数学/英语/物理/化学/生物/历史/地理/政治",
  "grade": "高一/高二/高三",
  "exam_type": "月考/期中/期末/模拟/高考真题/竞赛",
  "total_score": 150,
  "exam_date": null,
  "description": "简要描述",
  "questions": [
    {{
      "question_number": 1,
      "question_type": "选择题/填空题/解答题/实验题/作文题",
      "content": "题干完整内容",
      "options": "A. ...\nB. ...\nC. ...\nD. ...",
      "correct_answer": "如果原文有答案则填写，否则为空",
      "analysis": "如果原文有解析则填写，否则为空",
      "knowledge_point": "知识点",
      "score": 5
    }}
  ]
}}

要求：
1. 尽量提取所有能看清的题目，至少提取前 20 题。
2. 不要编造看不清的题目；看不清时只提取能确定的内容。
3. 只返回 JSON，不要 Markdown，不要解释。"""

        result = get_analyzer().chat(prompt)
        parsed = _json_from_text(result)
        if not parsed:
            print(f"AI题目识别返回无法解析: {str(result)[:500]}")
        return parsed

    @staticmethod
    def recognize_exam(file_path, use_ai=True):
        result = original_recognize_exam(file_path, use_ai=use_ai)
        ai_analysis = result.get('ai_analysis') or {}

        raw_questions = []
        if isinstance(ai_analysis, dict):
            raw_questions = ai_analysis.get('questions') or []

        normalized = []
        for index, raw in enumerate(raw_questions, start=1):
            question = _normalize_question(raw, index)
            if question:
                normalized.append(question)

        if normalized:
            existing = result.get('questions') or []
            if len(normalized) > len(existing):
                result['questions'] = normalized
            print(f"AI题目识别成功: {len(result.get('questions') or [])} 题")
        else:
            print('AI没有返回可入库的题目列表，将使用OCR基础提取结果')

        return result

    recognizer.analyze_with_ai = analyze_with_ai
    recognizer.recognize_exam = recognize_exam
    recognizer._question_ai_patched = True
    print('Uploaded exam AI question extraction patch is enabled')


def _import_with_question_recognition_patch(name, globals=None, locals=None, fromlist=(), level=0):
    module = _original_import(name, globals, locals, fromlist, level)
    if name == 'exam_recognizer':
        _patch_exam_recognizer(module)
    return module


builtins.__import__ = _import_with_question_recognition_patch
