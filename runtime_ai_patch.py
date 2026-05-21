#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runtime AI compatibility patch for cloud deployments.

The upload recognizer calls AIAnalyzer.chat(), but the original chat() method
only handled OpenAI-compatible providers. This patch makes recognition work with
other configured providers and lets cloud deployments use environment variables
for AI settings.
"""

import builtins
import json
import os
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


def _patch_ai_analyzer(module):
    cls = getattr(module, 'AIAnalyzer', None)
    if not cls or getattr(cls, '_runtime_ai_patched', False):
        return

    def chat(self, message, context=None):
        print(f"[AI] Provider: {self.provider}, Model: {self.model}, Base URL: {self.base_url}")
        messages = (context or []) + [{'role': 'user', 'content': message}]

        try:
            if not self.api_key and self.provider != 'local':
                return '错误: AI API Key 未配置'

            if self.provider in ['openai', 'deepseek', 'moonshot']:
                import requests
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': self.model,
                    'messages': messages,
                    'max_tokens': 4000,
                    'temperature': 0.3
                }
                response = requests.post(
                    f'{self.base_url}/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=120
                )
                print(f"[AI] Response status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                print(f"[AI] Error response: {response.text[:500]}")
                return f"错误: API返回状态码 {response.status_code}: {response.text[:200]}"

            if self.provider == 'claude':
                result = self._call_claude(message, image_paths=None)
            elif self.provider == 'qwen':
                result = self._call_qwen(message, image_paths=None)
            elif self.provider == 'zhipu':
                result = self._call_zhipu(message, image_paths=None)
            elif self.provider == 'local':
                result = self._call_local(message, image_paths=None)
            else:
                result = self._call_openai_compatible(message, image_paths=None)

            if isinstance(result, dict) and result.get('success'):
                return result.get('content', '')
            if isinstance(result, dict):
                return f"错误: {result.get('error', 'AI调用失败')}"
            return str(result or '')
        except Exception as exc:
            print(f"[AI] Exception: {exc}")
            return f"错误: {exc}"

    def get_analyzer():
        from database import get_config

        provider = os.environ.get('AI_PROVIDER') or get_config('ai_provider', 'openai')
        provider = (provider or 'openai').strip().lower()

        provider_key_env = {
            'openai': 'OPENAI_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'qwen': 'DASHSCOPE_API_KEY',
            'zhipu': 'ZHIPU_API_KEY',
            'moonshot': 'MOONSHOT_API_KEY',
            'claude': 'ANTHROPIC_API_KEY',
        }
        api_key = (
            os.environ.get('AI_API_KEY')
            or os.environ.get(provider_key_env.get(provider, ''), '')
            or get_config('ai_api_key', '')
        )
        model = os.environ.get('AI_MODEL') or get_config('ai_model', 'gpt-4')
        base_url = os.environ.get('AI_BASE_URL') or get_config('ai_base_url')

        return cls(provider, api_key, model, base_url)

    cls.chat = chat
    cls._runtime_ai_patched = True
    module.get_analyzer = get_analyzer


def _patch_exam_recognizer(module):
    recognizer = getattr(module, 'ExamRecognizer', None)
    if not recognizer or getattr(recognizer, '_runtime_ai_patched', False):
        return

    def analyze_with_ai(text, file_paths=None):
        from ai_analyzer import get_analyzer

        prompt = f"""请分析以下试卷内容，提取关键信息并以JSON格式返回：

试卷内容：
{text[:5000]}

请返回以下JSON字段：
{{
  "title": "试卷标题",
  "subject": "学科（语文/数学/英语/物理/化学/生物/历史/地理/政治）",
  "grade": "年级（高一/高二/高三）",
  "exam_type": "考试类型（月考/期中/期末/模拟/高考真题/竞赛）",
  "total_score": 150,
  "exam_date": null,
  "description": "试卷简要描述",
  "knowledge_points": ["知识点1", "知识点2"],
  "difficulty": "简单/中等/困难"
}}

只返回JSON，不要返回其他内容。"""
        result = get_analyzer().chat(prompt)
        parsed = _json_from_text(result)
        if not parsed:
            print(f"AI识别返回无法解析: {str(result)[:300]}")
        return parsed

    def analyze_pdf_with_ai(pdf_path):
        try:
            import fitz
            from ai_analyzer import get_analyzer

            doc = fitz.open(pdf_path)
            full_text = ''.join(page.get_text() for page in doc)
            doc.close()

            if not full_text or len(full_text.strip()) < 10:
                print('PDF文字提取失败，内容太少')
                return None

            prompt = f"""请分析以下试卷内容，提取试卷信息并只返回JSON：

试卷内容：
{full_text[:5000]}

JSON字段：title, subject, grade, exam_type, total_score, exam_date, description。"""
            return _json_from_text(get_analyzer().chat(prompt))
        except Exception as exc:
            print(f"AI PDF分析失败: {exc}")
            return None

    recognizer.analyze_with_ai = staticmethod(analyze_with_ai)
    recognizer.analyze_pdf_with_ai = staticmethod(analyze_pdf_with_ai)
    recognizer._runtime_ai_patched = True


def _import_with_ai_patch(name, globals=None, locals=None, fromlist=(), level=0):
    module = _original_import(name, globals, locals, fromlist, level)
    if name == 'ai_analyzer':
        _patch_ai_analyzer(module)
    elif name == 'exam_recognizer':
        _patch_exam_recognizer(module)
    return module


builtins.__import__ = _import_with_ai_patch
