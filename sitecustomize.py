#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Runtime hooks for uploaded Gaokao question auto-classification.

Python imports sitecustomize automatically during startup when this file is on
sys.path. The hook keeps the existing upload flow unchanged: when recognized
questions are saved through database.add_question, a classified copy is also
added to the Gaokao question bank.
"""

import builtins
import re


_original_import = builtins.__import__


SUBJECT_KEYWORD_RULES = {
    '数学': {
        '函数与导数': ['函数', '导数', '单调', '极值', '最值', '零点', '切线', 'f(x)', 'g(x)'],
        '三角函数': ['三角', '正弦', '余弦', 'tan', 'sin', 'cos', '解三角形'],
        '数列': ['数列', '等差', '等比', '通项', '前n项和'],
        '立体几何': ['立体几何', '空间', '棱锥', '棱柱', '球', '二面角', '体积'],
        '解析几何': ['椭圆', '双曲线', '抛物线', '圆', '直线', '焦点', '离心率'],
        '概率与统计': ['概率', '统计', '随机', '分布列', '期望', '方差', '样本'],
        '不等式': ['不等式', '恒成立', '取值范围', '均值'],
        '向量': ['向量', '数量积', '坐标表示'],
        '复数': ['复数', '虚数', 'z=', 'i'],
    },
    '语文': {
        '现代文阅读': ['阅读', '文本', '论述', '小说', '散文', '材料'],
        '古诗文阅读': ['文言', '诗歌', '默写', '翻译', '古代'],
        '语言文字运用': ['成语', '病句', '衔接', '压缩', '补写'],
        '写作': ['作文', '写作', '立意', '材料作文'],
    },
    '英语': {
        '阅读理解': ['read', 'passage', 'according to', 'main idea', 'paragraph'],
        '完形填空': ['cloze', 'blank', 'choose the best answer'],
        '语法填空': ['grammar', 'proper form', 'fill in'],
        '短文改错': ['correct', 'mistake', 'error'],
        '书面表达': ['write', 'letter', 'essay', 'composition'],
        '七选五': ['seven', 'five', 'A-G'],
    },
    '物理': {
        '力学': ['受力', '加速度', '速度', '位移', '牛顿', '动能', '动量', '机械能', '圆周运动'],
        '电磁学': ['电场', '磁场', '电流', '电压', '电阻', '感应', '洛伦兹', '安培'],
        '热学': ['气体', '温度', '内能', '热力学', '压强'],
        '光学': ['光', '折射', '反射', '干涉', '衍射'],
        '原子物理': ['原子', '原子核', '放射性', '光电效应'],
        '实验题': ['实验', '测量', '误差', '数据处理'],
    },
    '化学': {
        '有机化学': ['有机', '烃', '醇', '醛', '羧酸', '酯', '同分异构', '有机推断'],
        '无机化学': ['金属', '非金属', '离子', '氧化还原', '沉淀'],
        '化学反应原理': ['平衡', '电离', '水解', '电化学', '反应热', '速率'],
        '化学实验': ['实验', '装置', '检验', '分离', '除杂', '滴定'],
        '物质结构': ['原子结构', '分子结构', '晶体', '周期律', '化学键'],
    },
    '生物': {
        '细胞生物学': ['细胞', '线粒体', '叶绿体', '细胞膜', '有丝分裂'],
        '遗传学': ['遗传', '基因', '染色体', 'DNA', '杂交', '表现型', '基因型'],
        '生态学': ['生态', '种群', '群落', '生态系统', '食物链'],
        '动物生理': ['神经', '体液', '免疫', '内环境', '激素'],
        '植物生理': ['光合作用', '呼吸作用', '植物激素', '蒸腾'],
        '生物技术': ['基因工程', '细胞工程', '发酵', 'PCR', '酶工程'],
    },
    '历史': {
        '中国古代史': ['秦', '汉', '唐', '宋', '元', '明', '清', '科举', '君主专制'],
        '中国近代史': ['鸦片战争', '洋务', '辛亥', '五四', '抗日'],
        '中国现代史': ['新中国', '改革开放', '社会主义建设'],
        '世界近代史': ['文艺复兴', '工业革命', '启蒙', '资产阶级革命'],
        '世界现代史': ['一战', '二战', '冷战', '多极化'],
    },
    '地理': {
        '自然地理': ['地球运动', '大气', '水循环', '地貌', '气候', '自然带'],
        '人文地理': ['人口', '城市', '农业', '工业', '交通', '产业'],
        '区域地理': ['区域', '中国地理', '世界地理', '区位'],
        '地理信息技术': ['遥感', 'GPS', 'GIS', '地理信息'],
    },
    '政治': {
        '经济生活': ['消费', '生产', '市场', '价格', '货币', '分配'],
        '政治生活': ['公民', '政府', '人大', '政党', '民族', '国际关系'],
        '文化生活': ['文化', '传统', '民族精神', '文化建设'],
        '生活与哲学': ['唯物', '认识论', '辩证法', '矛盾', '价值观'],
    },
}


def _normalize_text(value):
    return str(value or '').strip()


def _infer_question_type(content, fallback='解答题'):
    try:
        from gaokao_classifier import classify_question_type
        return classify_question_type(content or '') or fallback
    except Exception:
        if re.search(r'[A-D][.、．]', content or '') or '下列' in (content or ''):
            return '选择题'
        if re.search(r'_{3,}|____|\(\s*\)', content or '') or '填空' in (content or ''):
            return '填空题'
        return fallback or '解答题'


def _infer_difficulty(content, score=None):
    try:
        from gaokao_classifier import estimate_difficulty
        return estimate_difficulty(content or '', score=score)
    except Exception:
        text_len = len(content or '')
        if text_len < 120:
            return '简单'
        if text_len < 360:
            return '中等'
        return '困难'


def _infer_category_and_points(subject, content):
    text = _normalize_text(content).lower()
    rules = SUBJECT_KEYWORD_RULES.get(subject, {})
    best_category = ''
    best_hits = []

    for category, keywords in rules.items():
        hits = [kw for kw in keywords if kw.lower() in text]
        if len(hits) > len(best_hits):
            best_category = category
            best_hits = hits

    if best_category:
        return best_category, '、'.join(best_hits[:4] or [best_category])

    try:
        from gaokao_classifier import SUBJECT_CATEGORIES
        categories = SUBJECT_CATEGORIES.get(subject, {}).get('一级分类', [])
        if categories:
            return categories[0], '待人工确认'
    except Exception:
        pass

    return '未分类', '待人工确认'


def _patch_search_gaokao_questions(module):
    original_search = getattr(module, 'search_gaokao_questions', None)
    if not original_search or getattr(original_search, '_accepts_upload_filters', False):
        return

    def search_gaokao_questions(subject=None, category=None, year=None, difficulty=None,
                                keyword=None, knowledge_point=None, question_type=None,
                                limit=100, page=None, per_page=20):
        conn = module.get_connection()
        query = 'SELECT * FROM gaokao_questions WHERE 1=1'
        count_query = 'SELECT COUNT(*) as cnt FROM gaokao_questions WHERE 1=1'
        params = []

        filters = [
            ('subject=%s', subject),
            ('category=%s', category),
            ('year=%s', year),
            ('difficulty=%s', difficulty),
            ('question_type=%s', question_type),
        ]
        for clause, value in filters:
            if value:
                query += f' AND {clause}'
                count_query += f' AND {clause}'
                params.append(value)

        if knowledge_point:
            query += ' AND knowledge_point LIKE %s'
            count_query += ' AND knowledge_point LIKE %s'
            params.append(f'%{knowledge_point}%')
        if keyword:
            query += ' AND (content LIKE %s OR knowledge_point LIKE %s)'
            count_query += ' AND (content LIKE %s OR knowledge_point LIKE %s)'
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        cur = module._execute(conn, count_query, params)
        total = module._fetchone(cur)['cnt']

        if page:
            offset = (page - 1) * per_page
            query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
            params.extend([per_page, offset])
        else:
            query += ' ORDER BY created_at DESC LIMIT %s'
            params.append(limit)

        cur = module._execute(conn, query, params)
        results = module._fetchall(cur)
        conn.close()

        if page:
            return {
                'items': results,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page,
                'has_prev': page > 1,
                'has_next': page * per_page < total,
                'prev_num': page - 1 if page > 1 else None,
                'next_num': page + 1 if page * per_page < total else None,
            }
        return {'items': results, 'total': total}

    search_gaokao_questions._accepts_upload_filters = True
    module.search_gaokao_questions = search_gaokao_questions


def _patch_database_module(module):
    if getattr(module, '_gaokao_upload_auto_classification_patched', False):
        _patch_search_gaokao_questions(module)
        return

    original_add_question = getattr(module, 'add_question', None)
    if not original_add_question:
        return

    def add_question(exam_id, question_number, question_type='选择题', content=None,
                     answer=None, score=0, user_answer=None, user_score=None):
        qid = original_add_question(
            exam_id=exam_id,
            question_number=question_number,
            question_type=question_type,
            content=content,
            answer=answer,
            score=score,
            user_answer=user_answer,
            user_score=user_score,
        )

        try:
            text = _normalize_text(content)
            exam = module.get_exam_by_id(exam_id) if hasattr(module, 'get_exam_by_id') else None
            subject = (exam or {}).get('subject') or ''
            if not text or subject not in SUBJECT_KEYWORD_RULES:
                return qid

            inferred_type = _infer_question_type(text, question_type)
            category, knowledge_point = _infer_category_and_points(subject, text)
            difficulty = _infer_difficulty(text, score)
            source_title = (exam or {}).get('title') or '上传试卷'

            module.add_gaokao_question(
                subject=subject,
                category=category,
                year=None,
                region=(exam or {}).get('exam_type') or '',
                question_number=question_number,
                question_type=inferred_type,
                content=text,
                options=None,
                correct_answer=answer,
                analysis='上传后自动分类生成',
                knowledge_point=knowledge_point,
                difficulty=difficulty,
                score=score,
                source=source_title,
            )
        except Exception as exc:
            print(f'高考试题自动分类失败: {exc}')

        return qid

    module.add_question = add_question
    _patch_search_gaokao_questions(module)
    module._gaokao_upload_auto_classification_patched = True


def _import_with_gaokao_classification_patch(name, globals=None, locals=None, fromlist=(), level=0):
    module = _original_import(name, globals, locals, fromlist, level)
    if name == 'database':
        _patch_database_module(module)
    return module


builtins.__import__ = _import_with_gaokao_classification_patch
