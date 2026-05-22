#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - AI分析模块"""

import json
import os
import requests
from datetime import datetime

class AIAnalyzer:
    """AI分析器，支持多种大模型"""
    
    def __init__(self, provider='openai', api_key='', model='gpt-4', base_url=None):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self._get_default_base_url()).rstrip('/')
    
    def _get_default_base_url(self):
        urls = {
            'openai': 'https://api.openai.com/v1',
            'claude': 'https://api.anthropic.com',
            'deepseek': 'https://api.deepseek.com',
            'qwen': 'https://dashscope.aliyuncs.com/api/v1',
            'zhipu': 'https://open.bigmodel.cn/api/paas/v4',
            'moonshot': 'https://api.moonshot.cn/v1',
            'local': 'http://localhost:11434/api',
        }
        return urls.get(self.provider, urls['openai'])
    
    def analyze_exam(self, exam_info, questions=None, image_paths=None, analysis_type='综合分析', exam_text=None):
        """分析试卷"""
        prompt = self._build_prompt(exam_info, questions, image_paths, analysis_type, exam_text)
        
        try:
            if self.provider in ['openai', 'moonshot']:
                return self._call_openai_compatible(prompt, image_paths)
            elif self.provider == 'claude':
                return self._call_claude(prompt, image_paths)
            elif self.provider == 'qwen':
                return self._call_qwen(prompt, image_paths)
            elif self.provider == 'zhipu':
                return self._call_zhipu(prompt, image_paths)
            elif self.provider == 'local':
                return self._call_local(prompt, image_paths)
            else:
                # DeepSeek等不支持vision的provider，只用文字分析
                return self._call_openai_compatible(prompt, image_paths=None)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _build_prompt(self, exam_info, questions, image_paths, analysis_type, exam_text=None):
        """构建提示词"""
        # 如果有试卷文字内容，附加到题目信息中
        text_content = ''
        if exam_text:
            text_content = f"\n\n试卷文字内容（从PDF/OCR提取）：\n{exam_text[:3000]}"

        prompts = {
            '综合分析': f"""你是一位经验丰富的高中教师，请对以下试卷进行综合分析：

试卷信息：
- 标题：{exam_info.get('title', '未知')}
- 科目：{exam_info.get('subject', '未知')}
- 年级：{exam_info.get('grade', '高中')}
- 考试类型：{exam_info.get('exam_type', '月考')}
- 总分：{exam_info.get('total_score', 150)}

题目信息：
{json.dumps(questions, ensure_ascii=False, indent=2) if questions else '暂无题目信息'}
{text_content}

请从以下角度进行分析：
1. 试卷难度评估（简单/中等/困难）
2. 知识点分布分析
3. 题型结构分析
4. 重点考点总结
5. 学生常见易错点
6. 复习建议

请用中文回答，格式清晰，使用Markdown格式。""",

            '错题分析': f"""你是一位经验丰富的高中教师，请对以下错题进行详细分析：

试卷信息：{exam_info.get('title', '未知')} - {exam_info.get('subject', '未知')}

题目信息：
{json.dumps(questions, ensure_ascii=False, indent=2) if questions else '暂无题目信息'}
{text_content}

请对每道错题进行：
1. 错误原因分析
2. 正确解题思路
3. 相关知识点讲解
4. 类似题目练习建议
5. 记忆技巧

请用中文回答，格式清晰。""",

            '学习建议': f"""你是一位专业的学习规划师，请根据以下考试情况给出学习建议：

学生信息：
- 科目：{exam_info.get('subject', '未知')}
- 考试类型：{exam_info.get('exam_type', '月考')}
- 总分：{exam_info.get('total_score', 150)}

请给出：
1. 短期（1-2周）学习计划
2. 中期（1个月）提升方案
3. 长期（一学期）学习规划
4. 每日学习时间分配建议
5. 推荐学习资源
6. 心理调节建议

请用中文回答，实用性强，可操作。""",

            '知识点总结': f"""你是一位经验丰富的高中教师，请总结以下试卷涉及的知识点：

试卷信息：
- 标题：{exam_info.get('title', '未知')}
- 科目：{exam_info.get('subject', '未知')}
{text_content}

请总结：
1. 核心知识点列表
2. 各知识点的考察频率
3. 知识点之间的关联
4. 重点难点标注
5. 相关公式/定理/概念

请用中文回答，使用思维导图式的层级结构。""",

            '错题提取与分析': f"""你是一位经验丰富的高中教师，请分析以下试卷并提取其中的典型错题和难题。

试卷信息：
- 标题：{exam_info.get('title', '未知')}
- 科目：{exam_info.get('subject', '未知')}
- 年级：{exam_info.get('grade', '高中')}

题目信息：
{json.dumps(questions, ensure_ascii=False, indent=2) if questions else '暂无题目信息，请根据试卷图片识别'}
{text_content}

请完成以下任务：
1. 识别试卷中的典型错题和难题（选择3-5道最具代表性的题目）
2. 对每道题进行详细分析

请严格按照以下JSON格式返回，不要返回其他内容：
{{
    "mistakes": [
        {{
            "question_number": 1,
            "question_type": "选择题/填空题/解答题",
            "content": "题目内容",
            "correct_answer": "正确答案",
            "common_wrong_answer": "学生常见错误答案",
            "error_analysis": "错误原因分析",
            "knowledge_point": "涉及的知识点",
            "solution_steps": "解题步骤和思路",
            "difficulty": "简单/中等/困难"
        }}
    ],
    "summary": "整体分析总结"
}}

只返回JSON，不要其他内容。"""
        }
        
        return prompts.get(analysis_type, prompts['综合分析'])
    
    def _call_openai_compatible(self, prompt, image_paths=None):
        """调用OpenAI兼容API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = [{'role': 'user', 'content': []}]
        
        # 添加文本
        messages[0]['content'].append({
            'type': 'text',
            'text': prompt
        })
        
        # 添加图片
        if image_paths:
            for img_path in image_paths:
                if img_path.startswith(('http://', 'https://')):
                    # URL直接使用
                    messages[0]['content'].append({
                        'type': 'image_url',
                        'image_url': {'url': img_path}
                    })
                elif img_path.startswith('data:'):
                    # 已经是base64 data URI，直接使用
                    messages[0]['content'].append({
                        'type': 'image_url',
                        'image_url': {'url': img_path}
                    })
                else:
                    # 本地文件，读取并转base64
                    import base64
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode()
                    messages[0]['content'].append({
                        'type': 'image_url',
                        'image_url': {'url': f'data:image/jpeg;base64,{img_data}'}
                    })
        
        # 如果没有图片，简化格式
        if not image_paths:
            messages = [{'role': 'user', 'content': prompt}]
        
        data = {
            'model': self.model,
            'messages': messages,
            'max_tokens': 4000,
            'temperature': 0.7
        }
        
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return {'success': True, 'content': content, 'model': self.model}
        else:
            return {'success': False, 'error': f'API调用失败: {response.status_code} - {response.text}'}
    
    def _call_claude(self, prompt, image_paths=None):
        """调用Claude API"""
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
        
        messages = [{'role': 'user', 'content': []}]
        messages[0]['content'].append({'type': 'text', 'text': prompt})
        
        if image_paths:
            for img_path in image_paths:
                import base64
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode()
                messages[0]['content'].append({
                    'type': 'image',
                    'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': img_data}
                })
        
        data = {
            'model': self.model,
            'max_tokens': 4000,
            'messages': messages
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            return {'success': True, 'content': content, 'model': self.model}
        else:
            return {'success': False, 'error': f'Claude API调用失败: {response.status_code}'}
    
    def _call_qwen(self, prompt, image_paths=None):
        """调用通义千问API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = [{'role': 'user', 'content': prompt}]
        
        data = {
            'model': self.model,
            'input': {'messages': messages},
            'parameters': {'max_tokens': 4000, 'temperature': 0.7}
        }
        
        response = requests.post(
            'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['output']['choices'][0]['message']['content']
            return {'success': True, 'content': content, 'model': self.model}
        else:
            return {'success': False, 'error': f'通义千问API调用失败: {response.status_code}'}
    
    def _call_zhipu(self, prompt, image_paths=None):
        """调用智谱AI API"""
        import jwt
        
        def generate_token():
            api_key = self.api_key
            if '.' in api_key:
                id_part, secret = api_key.split('.', 1)
            else:
                return api_key
            
            payload = {
                'api_key': id_part,
                'exp': int(datetime.now().timestamp()) + 3600,
                'timestamp': int(datetime.now().timestamp())
            }
            return jwt.encode(payload, secret, algorithm='HS256')
        
        headers = {
            'Authorization': f'Bearer {generate_token()}',
            'Content-Type': 'application/json'
        }
        
        messages = [{'role': 'user', 'content': prompt}]
        
        data = {
            'model': self.model,
            'messages': messages,
            'max_tokens': 4000,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return {'success': True, 'content': content, 'model': self.model}
        else:
            return {'success': False, 'error': f'智谱AI API调用失败: {response.status_code}'}
    
    def _call_local(self, prompt, image_paths=None):
        """调用本地模型（Ollama等）"""
        data = {
            'model': self.model,
            'prompt': prompt,
            'stream': False
        }
        
        response = requests.post(
            f'{self.base_url}/generate',
            json=data,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            return {'success': True, 'content': result.get('response', ''), 'model': self.model}
        else:
            return {'success': False, 'error': f'本地模型调用失败: {response.status_code}'}
    
    def chat(self, message, context=None):
        """通用对话接口"""
        print(f"[AI] Provider: {self.provider}, Model: {self.model}, Base URL: {self.base_url}")
        if context:
            messages = context + [{'role': 'user', 'content': message}]
        else:
            messages = [{'role': 'user', 'content': message}]
        
        try:
            if self.provider in ['openai', 'deepseek', 'moonshot']:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': self.model,
                    'messages': messages,
                    'max_tokens': 4000,
                    'temperature': 0.7
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
                else:
                    print(f"[AI] Error response: {response.text[:500]}")
                    return f"错误: API返回状态码 {response.status_code}"
            return "AI服务暂时不可用"
        except Exception as e:
            print(f"[AI] Exception: {e}")
            return f"错误: {str(e)}"
    
    def generate_practice_questions(self, mistake_info, num_questions=3):
        """根据错题生成练习题"""
        prompt = f"""你是一位经验丰富的高中教师，请根据以下错题信息生成{num_questions}道类似的练习题。

错题信息：
- 科目：{mistake_info.get('subject', '未知')}
- 题型：{mistake_info.get('question_type', '未知')}
- 题目内容：{mistake_info.get('content', '未知')}
- 正确答案：{mistake_info.get('correct_answer', '未知')}
- 错误分析：{mistake_info.get('analysis', '未知')}

要求：
1. 生成的题目要与原题类似，但不完全相同
2. 考察相同的知识点
3. 难度相当或略有变化
4. 每道题都要有详细的解析

请严格按照以下JSON格式返回，不要返回其他内容：
{{
    "questions": [
        {{
            "question_number": 1,
            "question_type": "选择题/填空题/解答题",
            "content": "题目内容",
            "options": "如果是选择题，提供选项A/B/C/D，否则为null",
            "correct_answer": "正确答案",
            "analysis": "详细解析"
        }}
    ]
}}

只返回JSON，不要其他内容。"""

        try:
            result = self.chat(prompt)
            # 解析JSON
            import re
            json_str = result.strip()
            if json_str.startswith('```'):
                json_str = json_str.split('\n', 1)[1] if '\n' in json_str else json_str[3:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            if json_str.startswith('json'):
                json_str = json_str[4:]
            
            return json.loads(json_str.strip())
        except Exception as e:
            print(f"生成练习题失败: {e}")
            return None


def get_analyzer():
    """获取AI分析器实例。
    优先级：环境变量 > 数据库配置 > 默认值"""
    from database import get_config, get_default_ai_config
    
    defaults = get_default_ai_config()
    
    # 环境变量优先，其次是数据库配置，最后是默认值
    def resolve(key, env_keys):
        for env_key in env_keys:
            val = os.environ.get(env_key)
            if val:
                return val
        db_val = get_config(key, None)
        if db_val:
            return db_val
        return defaults.get(key, '')
    
    provider = resolve('ai_provider', ['AI_PROVIDER'])
    api_key = resolve('ai_api_key', ['AI_API_KEY', 'DEEPSEEK_API_KEY'])
    model = resolve('ai_model', ['AI_MODEL', 'DEEPSEEK_MODEL'])
    base_url = resolve('ai_base_url', ['AI_BASE_URL', 'DEEPSEEK_BASE_URL'])
    
    return AIAnalyzer(provider, api_key, model, base_url)


if __name__ == '__main__':
    # 测试
    analyzer = AIAnalyzer('openai', 'test-key', 'gpt-4')
    print(f"AI分析器初始化完成: {analyzer.provider} - {analyzer.model}")
