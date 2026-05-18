#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - 试卷识别与自动分类模块"""

import os
import re
import json
import requests
from datetime import datetime

class ExamRecognizer:
    """试卷识别器，自动提取试卷信息"""
    
    # 学科关键词
    SUBJECT_KEYWORDS = {
        '语文': ['语文', '作文', '阅读理解', '古诗文', '文言文', '现代文', '作文题', '默写', '诗词'],
        '数学': ['数学', '函数', '方程', '几何', '代数', '概率', '导数', '三角', '向量', '数列', '不等式'],
        '英语': ['英语', 'English', '听力', '阅读', '完形', '作文', '语法', '词汇', '翻译'],
        '物理': ['物理', '力学', '电学', '电磁', '光学', '热学', '动能', '势能', '牛顿', '电路'],
        '化学': ['化学', '有机', '无机', '反应', '元素', '化合物', '氧化', '还原', '电解', '溶液'],
        '生物': ['生物', '细胞', '基因', '遗传', '进化', '生态', '蛋白质', 'DNA', 'RNA', '光合作用'],
        '历史': ['历史', '朝代', '改革', '革命', '战争', '条约', '文明', '古代', '近代', '现代'],
        '地理': ['地理', '气候', '地形', '洋流', '板块', '人口', '城市', '农业', '工业', '资源'],
        '政治': ['政治', '经济', '哲学', '法律', '制度', '权利', '义务', '民主', '法治', '市场']
    }
    
    # 年级关键词
    GRADE_KEYWORDS = {
        '高一': ['高一', '高中一年级', '必修一', '必修二', '必修1', '必修2'],
        '高二': ['高二', '高中二年级', '选择性必修', '选修'],
        '高三': ['高三', '高中三年级', '高考', '模拟', '冲刺']
    }
    
    # 考试类型关键词
    EXAM_TYPE_KEYWORDS = {
        '月考': ['月考', '月测', '阶段测试'],
        '期中': ['期中', '中期'],
        '期末': ['期末', '期末考试'],
        '模拟': ['模拟', '模考', '仿真'],
        '高考真题': ['高考', '全国卷', '新高考'],
        '竞赛': ['竞赛', '奥林匹克', '奥赛']
    }
    
    # 题型关键词
    QUESTION_TYPE_KEYWORDS = {
        '选择题': ['选择题', '选择', '单选', '多选', '不定项选择'],
        '填空题': ['填空题', '填空'],
        '解答题': ['解答题', '计算题', '证明题', '应用题', '简答题', '论述题'],
        '实验题': ['实验题', '实验'],
        '作文题': ['作文', '写作']
    }
    
    @staticmethod
    def extract_text_from_image(image_path):
        """从图片中提取文字（使用OCR）"""
        try:
            # 尝试使用pytesseract
            import pytesseract
            from PIL import Image
            
            # 设置tesseract路径（Windows）
            import os
            tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            image = Image.open(image_path)
            # 使用中文+英文识别
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            if text and text.strip():
                return text
        except ImportError:
            print("pytesseract未安装")
        except Exception as e:
            print(f"OCR识别出错: {e}")
        
        try:
            # 尝试使用百度OCR API
            result = ExamRecognizer._baidu_ocr(image_path)
            if result:
                return result
        except:
            pass
        
        return ""
    
    @staticmethod
    def _baidu_ocr(image_path):
        """使用百度OCR API识别文字"""
        import base64
        import requests
        
        # 这里需要配置百度OCR API Key
        from database import get_config
        api_key = get_config('baidu_ocr_api_key', '')
        secret_key = get_config('baidu_ocr_secret_key', '')
        
        if not api_key or not secret_key:
            return ""
        
        # 获取access_token
        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        token_resp = requests.post(token_url)
        access_token = token_resp.json().get('access_token')
        
        # 识别图片
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
        resp = requests.post(ocr_url, data={'image': image_data})
        
        if resp.status_code == 200:
            result = resp.json()
            words = [item['words'] for item in result.get('words_result', [])]
            return '\n'.join(words)
        
        return ""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path):
        """从PDF中提取文字"""
        text = ""
        
        # 方法1: 使用PyMuPDF提取文字
        try:
            import fitz
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            print(f"PyMuPDF提取失败: {e}")
        
        # 方法2: 使用PyPDF2
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            print(f"PyPDF2提取失败: {e}")
        
        # 方法3: 对扫描件PDF使用OCR
        try:
            import fitz
            import pytesseract
            from PIL import Image
            import tempfile
            
            # 设置tesseract路径
            tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            doc = fitz.open(pdf_path)
            ocr_text = ""
            
            # 对每一页进行OCR（最多5页）
            max_pages = min(5, len(doc))
            for page_num in range(max_pages):
                page = doc[page_num]
                # 转换为图片
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # 保存为临时文件
                temp_path = os.path.join(tempfile.gettempdir(), f'ocr_page_{page_num}.png')
                with open(temp_path, 'wb') as f:
                    f.write(img_data)
                
                # OCR识别
                image = Image.open(temp_path)
                page_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                ocr_text += page_text + "\n"
                
                # 清理临时文件
                os.remove(temp_path)
            
            doc.close()
            
            if ocr_text.strip():
                print(f"OCR识别成功，文字长度: {len(ocr_text)}")
                return ocr_text
                
        except Exception as e:
            print(f"OCR识别失败: {e}")
        
        return text
    
    @staticmethod
    def extract_text_from_docx(docx_path):
        """从Word文档中提取文字"""
        try:
            import docx
            doc = docx.Document(docx_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            pass
        
        return ""
    
    @staticmethod
    def extract_text(file_path):
        """根据文件类型提取文字"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return ExamRecognizer.extract_text_from_image(file_path)
        elif ext == '.pdf':
            return ExamRecognizer.extract_text_from_pdf(file_path)
        elif ext in ['.doc', '.docx']:
            return ExamRecognizer.extract_text_from_docx(file_path)
        
        return ""
    
    @staticmethod
    def recognize_subject(text):
        """识别学科"""
        text_lower = text.lower()
        scores = {}
        
        for subject, keywords in ExamRecognizer.SUBJECT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            if score > 0:
                scores[subject] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    @staticmethod
    def recognize_grade(text):
        """识别年级"""
        for grade, keywords in ExamRecognizer.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return grade
        return None
    
    @staticmethod
    def recognize_exam_type(text):
        """识别考试类型"""
        for exam_type, keywords in ExamRecognizer.EXAM_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return exam_type
        return None
    
    @staticmethod
    def recognize_total_score(text):
        """识别总分"""
        patterns = [
            r'总分[：:]\s*(\d+)\s*分',
            r'满分[：:]\s*(\d+)\s*分',
            r'共\s*(\d+)\s*分',
            r'(\d+)\s*分\s*满分',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        
        # 默认根据题型判断
        if '150分' in text or '150' in text:
            return 150.0
        elif '100分' in text or '100' in text:
            return 100.0
        
        return 150.0  # 默认150分
    
    @staticmethod
    def recognize_exam_date(text):
        """识别考试日期"""
        patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?',
            r'(\d{4})[年/-](\d{1,2})月',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3)) if len(match.groups()) > 2 else 1
                    if 2000 <= year <= 2100 and 1 <= month <= 12:
                        return f"{year}-{month:02d}-{day:02d}"
                except:
                    pass
        
        return None
    
    @staticmethod
    def extract_title(text):
        """提取试卷标题"""
        # 尝试从第一行提取标题
        lines = text.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # 检查是否包含年份、科目等关键词
                if any(keyword in line for keyword in ['年', '学期', '考试', '测试', '试卷', '检测']):
                    return line
        
        # 如果没找到，返回前30个字符
        first_line = lines[0].strip() if lines else "未命名试卷"
        return first_line[:50] if len(first_line) > 50 else first_line
    
    @staticmethod
    def extract_questions(text):
        """提取题目"""
        questions = []
        
        # 匹配题号模式
        patterns = [
            r'(\d+)[.、．]\s*(.*?)(?=\d+[.、．]|\Z)',
            r'[（(](\d+)[)）]\s*(.*?)(?=[（(]\d+[)）]|\Z)',
            r'第(\d+)题[：:]\s*(.*?)(?=第\d+题|\Z)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for num, content in matches:
                if len(content.strip()) > 5:
                    questions.append({
                        'number': int(num),
                        'content': content.strip()[:500],
                        'type': ExamRecognizer._guess_question_type(content)
                    })
        
        return questions
    
    @staticmethod
    def _guess_question_type(content):
        """猜测题型"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['选择', 'a.', 'b.', 'c.', 'd.', 'A.', 'B.', 'C.', 'D.']):
            return '选择题'
        elif any(keyword in content_lower for keyword in ['填空', '___', '（  ）', '(  )']):
            return '填空题'
        elif any(keyword in content_lower for keyword in ['计算', '证明', '解答', '求', '解']):
            return '解答题'
        elif any(keyword in content_lower for keyword in ['实验', '操作', '观察']):
            return '实验题'
        elif any(keyword in content_lower for keyword in ['作文', '写作', '不少于']):
            return '作文题'
        
        return '解答题'
    
    @staticmethod
    def analyze_with_ai(text, file_paths=None):
        """使用AI分析试卷内容"""
        from ai_analyzer import get_analyzer
        
        prompt = f"""请分析以下试卷内容，提取关键信息并以JSON格式返回：

试卷内容：
{text[:3000]}

请返回以下格式的JSON：
{{
    "title": "试卷标题",
    "subject": "学科（语文/数学/英语/物理/化学/生物/历史/地理/政治）",
    "grade": "年级（高一/高二/高三）",
    "exam_type": "考试类型（月考/期中/期末/模拟/高考真题/竞赛）",
    "total_score": 总分（数字）,
    "exam_date": "考试日期（YYYY-MM-DD格式，如果无法识别则为null）",
    "description": "试卷简要描述",
    "knowledge_points": ["知识点1", "知识点2"],
    "difficulty": "难度（简单/中等/困难）",
    "question_types": {{
        "选择题": 数量,
        "填空题": 数量,
        "解答题": 数量
    }}
}}

只返回JSON，不要其他内容。"""
        
        analyzer = get_analyzer()
        result = analyzer.chat(prompt)
        
        try:
            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            result = result.strip()
            if result.startswith('```'):
                result = result.split('\n', 1)[1] if '\n' in result else result[3:]
            if result.endswith('```'):
                result = result[:-3]
            if result.startswith('json'):
                result = result[4:]
            
            return json.loads(result.strip())
        except:
            return None
    
    @staticmethod
    def recognize_exam(file_path, use_ai=True):
        """综合识别试卷"""
        result = {
            'title': None,
            'subject': None,
            'grade': None,
            'exam_type': None,
            'total_score': 150.0,
            'exam_date': None,
            'description': None,
            'text': None,
            'questions': [],
            'ai_analysis': None
        }
        
        # 判断文件类型
        ext = os.path.splitext(file_path)[1].lower()
        is_image = ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        is_pdf = ext == '.pdf'
        
        print(f"开始识别试卷: {file_path}, 类型: {ext}")
        
        # 尝试OCR提取文字
        text = ""
        try:
            text = ExamRecognizer.extract_text(file_path)
            print(f"OCR提取文字长度: {len(text) if text else 0}")
        except Exception as e:
            print(f"OCR提取失败: {e}")
        
        result['text'] = text
        
        # 如果有文字，进行基础识别
        if text and len(text) > 10:
            result['title'] = ExamRecognizer.extract_title(text)
            result['subject'] = ExamRecognizer.recognize_subject(text)
            result['grade'] = ExamRecognizer.recognize_grade(text)
            result['exam_type'] = ExamRecognizer.recognize_exam_type(text)
            result['total_score'] = ExamRecognizer.recognize_total_score(text)
            result['exam_date'] = ExamRecognizer.recognize_exam_date(text)
            result['questions'] = ExamRecognizer.extract_questions(text)
            print(f"基础识别结果: 标题={result['title']}, 科目={result['subject']}")
        
        # 使用AI进行识别
        if use_ai:
            try:
                # 如果有文字，用AI分析文字
                if text and len(text) > 10:
                    print("使用AI分析OCR文字...")
                    ai_result = ExamRecognizer.analyze_with_ai(text, [file_path])
                elif is_pdf:
                    # PDF文件，用AI分析PDF
                    print("使用AI分析PDF...")
                    ai_result = ExamRecognizer.analyze_pdf_with_ai(file_path)
                elif is_image:
                    # 图片文件，尝试用AI分析图片（仅支持OpenAI）
                    print("尝试AI图片分析...")
                    ai_result = ExamRecognizer.analyze_image_with_ai(file_path)
                else:
                    ai_result = None
                
                if ai_result:
                    result['ai_analysis'] = ai_result
                    # 用AI结果补充或覆盖基础识别结果
                    if ai_result.get('title'):
                        result['title'] = ai_result['title']
                    if ai_result.get('subject'):
                        result['subject'] = ai_result['subject']
                    if ai_result.get('grade'):
                        result['grade'] = ai_result['grade']
                    if ai_result.get('exam_type'):
                        result['exam_type'] = ai_result['exam_type']
                    if ai_result.get('total_score'):
                        result['total_score'] = float(ai_result['total_score'])
                    if ai_result.get('exam_date'):
                        result['exam_date'] = ai_result['exam_date']
                    if ai_result.get('description'):
                        result['description'] = ai_result['description']
                    print(f"AI识别结果: 标题={result['title']}, 科目={result['subject']}")
            except Exception as e:
                print(f"AI识别失败: {e}")
        
        return result
    
    @staticmethod
    def analyze_image_with_ai(image_path):
        """使用AI视觉模型分析图片"""
        from ai_analyzer import get_analyzer
        import base64
        
        analyzer = get_analyzer()
        
        # 检查是否支持图片分析（只有部分模型支持）
        supported_providers = ['openai']
        if analyzer.provider not in supported_providers:
            # 不支持图片分析，使用OCR + 文字分析
            return None
        
        prompt = """请分析这张试卷图片，提取以下信息并以JSON格式返回：

1. title: 试卷标题
2. subject: 学科（语文/数学/英语/物理/化学/生物/历史/地理/政治）
3. grade: 年级（高一/高二/高三）
4. exam_type: 考试类型（月考/期中/期末/模拟/高考真题/竞赛）
5. total_score: 总分（数字）
6. exam_date: 考试日期（YYYY-MM-DD格式，如果无法识别则为null）
7. description: 试卷简要描述
8. text: 试卷中的主要文字内容（前500字）

请尽量准确识别。只返回JSON，不要其他内容。"""

        try:
            # 读取图片并转为base64
            with open(image_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode()
            
            # 构建带图片的消息
            messages = [{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_data}'}}
                ]
            }]
            
            # 调用AI
            headers = {
                'Authorization': f'Bearer {analyzer.api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': analyzer.model,
                'messages': messages,
                'max_tokens': 4000,
                'temperature': 0.3
            }
            response = requests.post(
                f'{analyzer.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=120
            )
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # 解析JSON
                content = content.strip()
                if content.startswith('```'):
                    content = content.split('\n', 1)[1] if '\n' in content else content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                if content.startswith('json'):
                    content = content[4:]
                
                return json.loads(content.strip())
            
            return None
        except Exception as e:
            print(f"AI图片分析失败: {e}")
            return None
    
    @staticmethod
    def analyze_pdf_with_ai(pdf_path):
        """使用AI分析PDF文件"""
        import fitz  # PyMuPDF
        
        try:
            from ai_analyzer import get_analyzer
            analyzer = get_analyzer()
            
            # 打开PDF提取文字
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
            
            if not full_text or len(full_text.strip()) < 10:
                print("PDF文字提取失败，内容太少")
                return None
            
            print(f"PDF提取文字长度: {len(full_text)}")
            
            # 使用AI分析文字内容
            prompt = f"""请分析以下试卷内容，提取信息并以JSON格式返回：

试卷内容：
{full_text[:3000]}

请提取以下信息：
1. title: 试卷标题
2. subject: 学科（语文/数学/英语/物理/化学/生物/历史/地理/政治）
3. grade: 年级（高一/高二/高三）
4. exam_type: 考试类型（月考/期中/期末/模拟/高考真题/竞赛）
5. total_score: 总分（数字）
6. exam_date: 考试日期（YYYY-MM-DD格式，如果无法识别则为null）
7. description: 试卷简要描述

只返回JSON，不要其他内容。"""

            result = analyzer.chat(prompt)
            
            # 解析JSON
            result = result.strip()
            if result.startswith('```'):
                result = result.split('\n', 1)[1] if '\n' in result else result[3:]
            if result.endswith('```'):
                result = result[:-3]
            if result.startswith('json'):
                result = result[4:]
            
            return json.loads(result.strip())
            
        except Exception as e:
            print(f"AI PDF分析失败: {e}")
            return None


def auto_recognize_and_save(file_path, user_id=None):
    """自动识别并保存试卷"""
    from database import add_exam, add_question, add_ai_analysis
    
    # 识别试卷
    result = ExamRecognizer.recognize_exam(file_path, use_ai=True)
    
    # 保存到数据库
    exam_id = add_exam(
        title=result.get('title') or '未命名试卷',
        subject=result.get('subject') or '其他',
        grade=result.get('grade'),
        exam_type=result.get('exam_type') or '其他',
        exam_date=result.get('exam_date'),
        total_score=result.get('total_score', 150),
        description=result.get('description'),
        file_path=file_path,
        file_type=os.path.splitext(file_path)[1][1:],
        upload_user_id=user_id
    )
    
    # 保存题目
    for q in result.get('questions', []):
        add_question(
            exam_id=exam_id,
            question_number=q.get('number'),
            question_type=q.get('type', '解答题'),
            content=q.get('content')
        )
    
    # 保存AI分析结果
    if result.get('ai_analysis'):
        add_ai_analysis(
            exam_id=exam_id,
            analysis_type='自动识别',
            content=json.dumps(result['ai_analysis'], ensure_ascii=False, indent=2),
            model_name='auto'
        )
    
    return {
        'exam_id': exam_id,
        'recognition_result': result
    }


if __name__ == '__main__':
    # 测试
    recognizer = ExamRecognizer()
    
    test_text = """
    2026年高一下学期数学期中考试试卷
    总分：150分  时间：120分钟
    
    一、选择题（每小题5分，共60分）
    1. 已知集合A={1,2,3}，B={2,3,4}，则A∩B=
    A. {1,2}  B. {2,3}  C. {3,4}  D. {1,4}
    
    二、填空题（每小题5分，共20分）
    13. 函数f(x)=x²+2x+1的最小值为______
    
    三、解答题（共70分）
    17. （10分）已知等差数列{an}中，a1=2，a3=6，求通项公式。
    """
    
    print("学科识别:", recognizer.recognize_subject(test_text))
    print("年级识别:", recognizer.recognize_grade(test_text))
    print("考试类型:", recognizer.recognize_exam_type(test_text))
    print("总分识别:", recognizer.recognize_total_score(test_text))
    print("标题提取:", recognizer.extract_title(test_text))
