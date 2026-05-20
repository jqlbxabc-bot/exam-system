#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small production route patches applied after Flask app startup."""


def apply_runtime_patches(flask_app):
    """Apply route-level fallbacks that keep user-facing pages available."""
    _patch_analysis_list_route(flask_app)


def _patch_analysis_list_route(flask_app):
    try:
        from flask import flash, redirect, render_template, request, session, url_for
        import database as db
    except Exception as exc:
        print(f'分析管理安全补丁加载失败: {exc}')
        return

    def _login_required_inline():
        if 'user' not in session:
            return redirect(url_for('login'))
        return None

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
        login_redirect = _login_required_inline()
        if login_redirect:
            return login_redirect

        exam_id = request.args.get('exam_id', type=int)
        analysis_type = request.args.get('analysis_type', '')
        analysis_types = ['综合分析', '知识点总结', '学习建议', '错题提取与分析', '错题分析', '自动识别']

        try:
            analyses = _fetch_analyses(
                exam_id=exam_id,
                analysis_type=analysis_type if analysis_type else None,
            )
        except Exception as exc:
            print(f'分析管理查询失败，已返回空列表: {exc}')
            flash('分析记录读取失败，已显示空列表。请稍后重试或检查数据库。', 'warning')
            analyses = []

        for analysis in analyses:
            analysis['content'] = analysis.get('content') or ''
            analysis['analysis_type'] = analysis.get('analysis_type') or '分析记录'
            analysis['exam_title'] = analysis.get('exam_title') or f"试卷#{analysis.get('exam_id', '')}"
            analysis['exam_subject'] = analysis.get('exam_subject') or ''

        return render_template(
            'analysis_list.html',
            analyses=analyses,
            analysis_types=analysis_types,
            selected_type=analysis_type,
            selected_exam_id=exam_id,
        )

    flask_app.view_functions['analysis_list'] = safe_analysis_list
    print('分析管理安全路由已启用')
