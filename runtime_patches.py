#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Production route patches applied after Flask app startup."""

import re
from collections import Counter, defaultdict

SUBJECTS = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
QUESTION_TYPES = ['选择题', '填空题', '解答题', '实验题', '作文题', '阅读理解', '计算题']
DIFFICULTIES = ['简单', '中等', '困难']

CATEGORY_KEYWORDS = {
    '数学': [('函数', '函数'), ('导数', '导数'), ('数列', '数列'), ('几何', '立体几何'), ('圆锥', '解析几何'), ('三角', '三角函数'), ('概率', '概率统计'), ('向量', '平面向量')],
    '语文': [('文言', '文言文'), ('阅读', '现代文阅读'), ('作文', '写作'), ('诗', '古诗词鉴赏'), ('语言', '语言文字运用')],
    '英语': [('阅读', '阅读理解'), ('完形', '完形填空'), ('语法', '语法填空'), ('作文', '写作'), ('听力', '听力')],
    '物理': [('力', '力学'), ('电', '电磁学'), ('磁', '电磁学'), ('能量', '能量守恒'), ('实验', '实验探究')],
    '化学': [('反应', '化学反应原理'), ('有机', '有机化学'), ('实验', '化学实验'), ('离子', '离子反应'), ('元素', '元素化合物')],
    '生物': [('遗传', '遗传与进化'), ('细胞', '细胞代谢'), ('生态', '生态系统'), ('实验', '实验探究'), ('免疫', '稳态与调节')],
    '历史': [('制度', '政治制度'), ('经济', '经济史'), ('文化', '思想文化'), ('改革', '改革史')],
    '地理': [('气候', '自然地理'), ('人口', '人文地理'), ('城市', '城市地理'), ('区域', '区域发展')],
    '政治': [('经济', '经济生活'), ('哲学', '哲学生活'), ('文化', '文化生活'), ('政治', '政治生活')],
}


def apply_runtime_patches(flask_app):
    """Apply route-level fallbacks and product upgrades."""
    _patch_analysis_list_route(flask_app)
    _patch_mistake_list_route(flask_app)
    _patch_practice_routes(flask_app)
    _patch_gaokao_list_route(flask_app)
    _register_recognition_review_route(flask_app)


def _safe_login_redirect(session, redirect, url_for):
    if 'user' not in session:
        return redirect(url_for('login'))
    return None


def _current_user(session):
    return session.get('user') or {}


def _infer_question_type(content):
    text = content or ''
    if re.search(r'(^|\n)\s*[A-D][\.|、]', text) or 'A.' in text or 'A、' in text:
        return '选择题'
    if '填空' in text or '____' in text or '___' in text or '（  ）' in text:
        return '填空题'
    if '实验' in text:
        return '实验题'
    if '作文' in text or '写作' in text:
        return '作文题'
    if any(word in text for word in ['解答', '证明', '计算', '求证', '分析']):
        return '解答题'
    return '解答题' if len(text) > 120 else '选择题'


def _infer_category(subject, content):
    text = content or ''
    for keyword, category in CATEGORY_KEYWORDS.get(subject or '', []):
        if keyword in text:
            return category
    return '未分类'


def _extract_knowledge(content, analysis=None):
    text = f"{content or ''}\n{analysis or ''}"
    match = re.search(r'知识点[：: ]+([^\n。；;]{1,40})', text)
    if match:
        return match.group(1).strip(' ，,')
    candidates = ['函数', '导数', '数列', '三角函数', '概率统计', '阅读理解', '文言文', '写作', '力学', '电磁学', '有机化学', '遗传', '自然地理', '经济生活']
    found = [word for word in candidates if word in text]
    return '、'.join(found[:3]) if found else ''


def _estimate_difficulty(content):
    text = content or ''
    if len(text) > 260 or any(word in text for word in ['综合', '证明', '探究', '压轴', '复杂']):
        return '困难'
    if len(text) < 90 and not any(word in text for word in ['证明', '分析', '实验']):
        return '简单'
    return '中等'


def _top_counter(items, key, limit=6):
    counter = Counter((item.get(key) or '未分类') for item in items)
    return [{'name': name, 'count': count} for name, count in counter.most_common(limit)]


def _weak_stats(mistakes):
    enriched = []
    for item in mistakes:
        item = dict(item)
        item['knowledge_point'] = _extract_knowledge(item.get('content'), item.get('analysis')) or '未标注知识点'
        created_at = item.get('created_at')
        item['created_date'] = str(created_at)[:10] if created_at else ''
        enriched.append(item)
    return {
        'subjects': _top_counter(enriched, 'subject'),
        'question_types': _top_counter(enriched, 'question_type'),
        'knowledge_points': _top_counter(enriched, 'knowledge_point'),
    }, enriched


def _fetch_gaokao_matches(db, subject=None, keyword=None, question_type=None, limit=10):
    conn = db.get_connection()
    try:
        params = []
        query = 'SELECT * FROM gaokao_questions WHERE 1=1'
        if subject:
            query += ' AND subject=%s'
            params.append(subject)
        if question_type:
            query += ' AND question_type=%s'
            params.append(question_type)
        if keyword:
            query += ' AND (content LIKE %s OR knowledge_point LIKE %s OR category LIKE %s)'
            like = f'%{keyword}%'
            params.extend([like, like, like])
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
        cur = db._execute(conn, query, params)
        return db._fetchall(cur)
    finally:
        conn.close()


def _patch_analysis_list_route(flask_app):
    try:
        from flask import flash, redirect, render_template, request, session, url_for
        import database as db
    except Exception as exc:
        print(f'分析管理安全补丁加载失败: {exc}')
        return

    def _fetch_analyses(exam_id=None, analysis_type=None, limit=100):
        conn = db.get_connection()
        try:
            params = []
            query = '''
                SELECT ai_analysis.*, exams.title AS exam_title, exams.subject AS exam_subject
                FROM ai_analysis
                LEFT JOIN exams ON exams.id = ai_analysis.exam_id
                WHERE 1=1
            '''
            if exam_id:
                query += ' AND ai_analysis.exam_id=%s'
                params.append(exam_id)
            if analysis_type:
                query += ' AND ai_analysis.analysis_type=%s'
                params.append(analysis_type)
            query += ' ORDER BY ai_analysis.created_at DESC LIMIT %s'
            params.append(limit)
            cur = db._execute(conn, query, params)
            return db._fetchall(cur)
        finally:
            conn.close()

    def safe_analysis_list():
        login_redirect = _safe_login_redirect(session, redirect, url_for)
        if login_redirect:
            return login_redirect

        exam_id = request.args.get('exam_id', type=int)
        analysis_type = request.args.get('analysis_type', '')
        analysis_types = ['综合分析', '知识点总结', '学习建议', '错题提取与分析', '错题分析', '自动识别']
        try:
            analyses = _fetch_analyses(exam_id=exam_id, analysis_type=analysis_type or None)
        except Exception as exc:
            print(f'分析管理查询失败，已返回空列表: {exc}')
            flash('分析记录读取失败，已显示空列表。请稍后重试或检查数据库。', 'warning')
            analyses = []

        for analysis in analyses:
            content = analysis.get('content') or ''
            analysis['content'] = content
            analysis['analysis_type'] = analysis.get('analysis_type') or '分析记录'
            analysis['exam_title'] = analysis.get('exam_title') or f"试卷#{analysis.get('exam_id', '')}"
            analysis['exam_subject'] = analysis.get('exam_subject') or ''
            analysis['status_label'] = '已完成' if content.strip() else '内容为空'
            analysis['status_class'] = 'success' if content.strip() else 'warning'
            analysis['source_label'] = analysis['exam_title'] if analysis.get('exam_id') else '系统生成'

        return render_template('analysis_list.html', analyses=analyses, analysis_types=analysis_types, selected_type=analysis_type, selected_exam_id=exam_id)

    flask_app.view_functions['analysis_list'] = safe_analysis_list
    print('分析管理安全路由已启用')


def _patch_mistake_list_route(flask_app):
    try:
        from flask import redirect, render_template, request, session, url_for
        import database as db
    except Exception as exc:
        print(f'错题本增强补丁加载失败: {exc}')
        return

    def enhanced_mistake_list():
        login_redirect = _safe_login_redirect(session, redirect, url_for)
        if login_redirect:
            return login_redirect
        user = _current_user(session)
        subject = request.args.get('subject', '')
        mistakes = db.get_mistakes_by_user(user.get('id'), subject=subject or None, limit=300)
        stats, mistakes = _weak_stats(mistakes)
        subjects = sorted({m.get('subject') for m in mistakes if m.get('subject')})
        return render_template('mistake_list.html', mistakes=mistakes, subjects=subjects, selected_subject=subject, mistake_stats=stats)

    flask_app.view_functions['mistake_list'] = enhanced_mistake_list
    print('错题本知识点统计已启用')


def _patch_practice_routes(flask_app):
    try:
        from flask import flash, redirect, render_template, request, session, url_for
        import database as db
    except Exception as exc:
        print(f'专项练习增强补丁加载失败: {exc}')
        return

    def enhanced_practice_list():
        login_redirect = _safe_login_redirect(session, redirect, url_for)
        if login_redirect:
            return login_redirect
        user = _current_user(session)
        subject = request.args.get('subject', '')
        status = request.args.get('status', '')
        sessions = db.get_practice_sessions_by_user(user.get('id'), subject=subject or None, status=status or None, limit=80)
        mistakes = db.get_mistakes_by_user(user.get('id'), limit=300)
        stats, _ = _weak_stats(mistakes)
        subjects = sorted({s.get('subject') for s in sessions if s.get('subject')} | {m.get('subject') for m in mistakes if m.get('subject')})
        return render_template('practice_list.html', sessions=sessions, subjects=subjects, selected_subject=subject, selected_status=status, weak_points=stats['knowledge_points'])

    def auto_generate_practice():
        login_redirect = _safe_login_redirect(session, redirect, url_for)
        if login_redirect:
            return login_redirect
        user = _current_user(session)
        subject = request.form.get('subject') or None
        keyword = (request.form.get('knowledge_point') or '').strip()
        question_type = request.form.get('question_type') or None
        count = request.form.get('count', type=int) or 8
        count = max(3, min(count, 20))

        mistakes = db.get_mistakes_by_user(user.get('id'), subject=subject, limit=300)
        stats, enriched = _weak_stats(mistakes)
        if not keyword and stats['knowledge_points']:
            keyword = stats['knowledge_points'][0]['name']
        if not subject and enriched:
            subject = Counter(m.get('subject') for m in enriched if m.get('subject')).most_common(1)[0][0]
        if not question_type and enriched:
            qtypes = Counter(m.get('question_type') for m in enriched if m.get('question_type')).most_common(1)
            question_type = qtypes[0][0] if qtypes else None

        matches = _fetch_gaokao_matches(db, subject=subject, keyword=None if keyword == '未标注知识点' else keyword, question_type=question_type, limit=count)
        if not matches:
            matches = _fetch_gaokao_matches(db, subject=subject, keyword=None, question_type=None, limit=count)
        if not matches and enriched:
            matches = [{'content': m.get('content'), 'question_type': m.get('question_type'), 'correct_answer': m.get('correct_answer'), 'analysis': m.get('analysis'), 'options': None} for m in enriched[:count]]
        if not matches:
            flash('还没有可用于生成练习的错题或真题。', 'warning')
            return redirect(url_for('practice_list'))

        title_bits = [subject or '综合', keyword or '薄弱点']
        session_id = db.create_practice_session(user.get('id'), subject=subject, practice_type='智能专项练习', title=' · '.join(title_bits))
        added = 0
        for index, q in enumerate(matches[:count], start=1):
            content = q.get('content') or ''
            if not content.strip():
                continue
            db.add_practice_question(
                session_id,
                question_number=index,
                question_type=q.get('question_type') or question_type or _infer_question_type(content),
                content=content,
                options=q.get('options'),
                correct_answer=q.get('correct_answer'),
                analysis=q.get('analysis'),
            )
            added += 1
        db.update_practice_session(session_id, total_questions=added)
        flash(f'已生成 {added} 道专项练习题。', 'success')
        return redirect(url_for('do_practice', session_id=session_id)) if added else redirect(url_for('practice_list'))

    flask_app.view_functions['practice_list'] = enhanced_practice_list
    if 'auto_generate_practice' not in flask_app.view_functions:
        flask_app.add_url_rule('/practice/auto-generate', 'auto_generate_practice', auto_generate_practice, methods=['POST'])
    print('智能专项练习已启用')


def _patch_gaokao_list_route(flask_app):
    try:
        from flask import redirect, render_template, request, session, url_for
        import database as db
    except Exception as exc:
        print(f'真题库筛选增强补丁加载失败: {exc}')
        return

    def enhanced_gaokao_list():
        login_redirect = _safe_login_redirect(session, redirect, url_for)
        if login_redirect:
            return login_redirect
        selected_subject = request.args.get('subject', '')
        selected_category = request.args.get('category', '')
        selected_difficulty = request.args.get('difficulty', '')
        selected_question_type = request.args.get('question_type', '')
        selected_year = request.args.get('year', type=int)
        keyword = request.args.get('keyword', '')
        knowledge_point = request.args.get('knowledge_point', '')

        conn = db.get_connection()
        try:
            params = []
            query = 'SELECT * FROM gaokao_questions WHERE 1=1'
            for field, value in [('subject', selected_subject), ('category', selected_category), ('difficulty', selected_difficulty), ('question_type', selected_question_type), ('year', selected_year)]:
                if value:
                    query += f' AND {field}=%s'
                    params.append(value)
            if keyword:
                query += ' AND (content LIKE %s OR knowledge_point LIKE %s OR analysis LIKE %s)'
                like = f'%{keyword}%'
                params.extend([like, like, like])
            if knowledge_point:
                query += ' AND knowledge_point LIKE %s'
                params.append(f'%{knowledge_point}%')
            query += ' ORDER BY created_at DESC LIMIT 200'
            questions = db._fetchall(db._execute(conn, query, params))
            stats = db._fetchall(db._execute(conn, 'SELECT subject, COUNT(*) AS count, MIN(year) AS min_year, MAX(year) AS max_year FROM gaokao_questions GROUP BY subject ORDER BY subject'))
        finally:
            conn.close()
        return render_template('gaokao_list.html', questions=questions, category_tree=db.get_gaokao_category_tree(), stats=stats, subjects=SUBJECTS, selected_subject=selected_subject, selected_category=selected_category, selected_difficulty=selected_difficulty, selected_question_type=selected_question_type, selected_year=selected_year, keyword=keyword, selected_knowledge_point=knowledge_point)

    flask_app.view_functions['gaokao_list'] = enhanced_gaokao_list
    print('真题库知识点筛选已启用')


def _register_recognition_review_route(flask_app):
    try:
        from flask import flash, redirect, render_template, request, session, url_for
        import database as db
    except Exception as exc:
        print(f'识别确认页补丁加载失败: {exc}')
        return

    def recognition_review(exam_id):
        login_redirect = _safe_login_redirect(session, redirect, url_for)
        if login_redirect:
            return login_redirect
        exam = db.get_exam_by_id(exam_id)
        if not exam:
            flash('试卷不存在。', 'warning')
            return redirect(url_for('exam_list'))
        questions = db.get_questions_by_exam(exam_id)
        prepared = []
        for q in questions:
            q = dict(q)
            q['suggested_type'] = q.get('question_type') or _infer_question_type(q.get('content'))
            q['suggested_category'] = _infer_category(exam.get('subject'), q.get('content'))
            q['suggested_knowledge'] = _extract_knowledge(q.get('content'), q.get('answer'))
            q['suggested_difficulty'] = _estimate_difficulty(q.get('content'))
            prepared.append(q)

        if request.method == 'POST':
            saved = 0
            for q in prepared:
                qid = q.get('id')
                content = q.get('content') or ''
                question_type = request.form.get(f'question_type_{qid}') or q['suggested_type']
                category = request.form.get(f'category_{qid}') or q['suggested_category']
                knowledge = request.form.get(f'knowledge_point_{qid}') or q['suggested_knowledge']
                difficulty = request.form.get(f'difficulty_{qid}') or q['suggested_difficulty']
                if not content.strip():
                    continue
                try:
                    db.update_question(qid, question_type=question_type)
                    db.add_gaokao_question(
                        subject=exam.get('subject') or '综合',
                        content=content,
                        category=category,
                        question_number=q.get('question_number'),
                        question_type=question_type,
                        correct_answer=q.get('answer'),
                        analysis='上传识别后确认入库',
                        knowledge_point=knowledge,
                        difficulty=difficulty,
                        score=q.get('score'),
                        source=exam.get('title'),
                    )
                    saved += 1
                except Exception as exc:
                    print(f'识别确认入库失败 question={qid}: {exc}')
            flash(f'已确认并入库 {saved} 道题。', 'success')
            return redirect(url_for('exam_detail', exam_id=exam_id))

        return render_template('recognition_review.html', exam=exam, questions=prepared, question_types=QUESTION_TYPES, difficulties=DIFFICULTIES)

    if 'recognition_review' not in flask_app.view_functions:
        flask_app.add_url_rule('/exams/<int:exam_id>/recognition-review', 'recognition_review', recognition_review, methods=['GET', 'POST'])
    print('上传识别确认页已启用')
