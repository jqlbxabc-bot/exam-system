#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Recognition diagnostics and rerun endpoints."""

import json
import os


def _first_existing_path(*paths):
    for path in paths:
        if path and isinstance(path, str) and not path.startswith(('http://', 'https://')) and os.path.exists(path):
            return path
    return None


def _exam_file_path(exam):
    if not exam:
        return None
    file_path = exam.get('file_path')
    if not file_path:
        return None
    return _first_existing_path(file_path, os.path.join(os.getcwd(), file_path))


def _question_payload(q):
    return {
        'number': q.get('number') or q.get('question_number'),
        'type': q.get('type') or q.get('question_type') or '解答题',
        'content': q.get('content') or '',
        'answer': q.get('answer') or q.get('correct_answer'),
        'score': q.get('score') or 0,
    }


def register_recognition_diagnostics(app):
    @app.route('/admin/recognition-diagnostics')
    def recognition_diagnostics():
        import database as db

        exams = db.get_all_exams(limit=10)
        rows = []
        for exam in exams:
            questions = db.get_questions_by_exam(exam['id'])
            analyses = db.get_all_ai_analyses(exam['id']) if hasattr(db, 'get_all_ai_analyses') else []
            path = _exam_file_path(exam)
            rows.append({
                'exam_id': exam['id'],
                'title': exam.get('title'),
                'subject': exam.get('subject'),
                'file_path': exam.get('file_path'),
                'file_exists': bool(path),
                'question_count': len(questions),
                'analysis_count': len(analyses),
                'latest_analysis_type': analyses[0].get('analysis_type') if analyses else '',
            })
        return {'exams': rows}

    @app.route('/admin/rerun-recognition/<int:exam_id>')
    def rerun_recognition(exam_id):
        import database as db
        from exam_recognizer import ExamRecognizer

        exam = db.get_exam_by_id(exam_id)
        if not exam:
            return {'success': False, 'error': '试卷不存在'}, 404

        path = _exam_file_path(exam)
        if not path:
            return {
                'success': False,
                'error': '试卷文件不存在。云托管本地上传文件可能在重新部署后丢失，请重新上传试卷。',
                'file_path': exam.get('file_path'),
            }, 400

        result = ExamRecognizer.recognize_exam(path, use_ai=True)
        questions = [_question_payload(q) for q in (result.get('questions') or [])]
        saved = 0
        for q in questions:
            content = (q.get('content') or '').strip()
            if not content:
                continue
            db.add_question(
                exam_id=exam_id,
                question_number=q.get('number'),
                question_type=q.get('type') or '解答题',
                content=content,
                answer=q.get('answer'),
                score=q.get('score') or 0,
            )
            saved += 1

        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            db.add_ai_analysis(
                exam_id=exam_id,
                analysis_type='重新识别',
                content=json.dumps(ai_analysis, ensure_ascii=False, indent=2),
                model_name='auto',
                question_count=len(questions),
            )

        text = result.get('text') or ''
        return {
            'success': True,
            'exam_id': exam_id,
            'file_path': path,
            'ocr_text_length': len(text),
            'ocr_text_preview': text[:500],
            'recognized_question_count': len(questions),
            'saved_question_count': saved,
            'title': result.get('title'),
            'subject': result.get('subject'),
            'ai_analysis_present': bool(ai_analysis),
        }
