#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - 数据库模块"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'exam_system.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'student',
        display_name TEXT,
        grade TEXT,
        class_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 试卷表
    c.execute('''CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        grade TEXT,
        exam_type TEXT DEFAULT '月考',
        exam_date TEXT,
        total_score REAL DEFAULT 150,
        description TEXT,
        file_path TEXT,
        file_type TEXT,
        cloud_url TEXT,
        upload_user_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (upload_user_id) REFERENCES users(id)
    )''')
    
    # 试卷图片/文件表
    c.execute('''CREATE TABLE IF NOT EXISTS exam_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT,
        cloud_url TEXT,
        file_type TEXT,
        page_number INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
    )''')
    
    # 题目表
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        question_number INTEGER,
        question_type TEXT DEFAULT '选择题',
        content TEXT,
        answer TEXT,
        score REAL DEFAULT 0,
        user_answer TEXT,
        user_score REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
    )''')
    
    # AI分析结果表
    c.execute('''CREATE TABLE IF NOT EXISTS ai_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        analysis_type TEXT DEFAULT '综合分析',
        content TEXT,
        model_name TEXT,
        difficulty TEXT,
        knowledge_summary TEXT,
        question_count INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
    )''')
    
    # 错题本表
    c.execute('''CREATE TABLE IF NOT EXISTS mistake_book (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER,
        exam_id INTEGER,
        subject TEXT,
        question_type TEXT,
        content TEXT,
        correct_answer TEXT,
        user_answer TEXT,
        analysis TEXT,
        mastery_level INTEGER DEFAULT 0,
        review_count INTEGER DEFAULT 0,
        next_review_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (exam_id) REFERENCES exams(id)
    )''')
    
    # 学习统计表
    c.execute('''CREATE TABLE IF NOT EXISTS study_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT,
        exam_date TEXT,
        score REAL,
        total_score REAL,
        rank INTEGER,
        class_avg REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 系统配置表
    c.execute('''CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key TEXT UNIQUE NOT NULL,
        config_value TEXT,
        description TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 练习会话表
    c.execute('''CREATE TABLE IF NOT EXISTS practice_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mistake_id INTEGER,
        subject TEXT,
        practice_type TEXT DEFAULT '错题巩固',
        title TEXT,
        total_questions INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0,
        status TEXT DEFAULT '进行中',
        score REAL,
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (mistake_id) REFERENCES mistake_book(id)
    )''')
    
    # 练习题目表
    c.execute('''CREATE TABLE IF NOT EXISTS practice_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        question_number INTEGER,
        question_type TEXT DEFAULT '解答题',
        content TEXT,
        options TEXT,
        correct_answer TEXT,
        user_answer TEXT,
        is_correct INTEGER DEFAULT 0,
        analysis TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE
    )''')
    
    # 改错记录表
    c.execute('''CREATE TABLE IF NOT EXISTS correction_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mistake_id INTEGER,
        practice_question_id INTEGER,
        session_id INTEGER,
        original_mistake TEXT,
        user_correction TEXT,
        is_correct INTEGER DEFAULT 0,
        teacher_comment TEXT,
        correction_count INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (mistake_id) REFERENCES mistake_book(id),
        FOREIGN KEY (practice_question_id) REFERENCES practice_questions(id),
        FOREIGN KEY (session_id) REFERENCES practice_sessions(id)
    )''')
    
    # 高考真题题库表
    c.execute('''CREATE TABLE IF NOT EXISTS gaokao_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        category TEXT DEFAULT '',
        year INTEGER,
        region TEXT,
        question_number INTEGER,
        question_type TEXT DEFAULT '选择题',
        content TEXT NOT NULL,
        options TEXT,
        correct_answer TEXT,
        analysis TEXT,
        knowledge_point TEXT,
        difficulty TEXT DEFAULT '中等',
        score REAL,
        source TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 学习计划表
    c.execute('''CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        subject TEXT,
        plan_type TEXT DEFAULT '日常学习',
        description TEXT,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        daily_goal TEXT,
        status TEXT DEFAULT '进行中',
        progress REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # 学习计划任务表
    c.execute('''CREATE TABLE IF NOT EXISTS plan_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plan_id) REFERENCES study_plans(id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()
    
    # 数据库迁移：给已有表添加新列（忽略已存在的列错误）
    _migrate_db()
    
    # 初始化默认配置
    init_default_config()

def _migrate_db():
    """数据库迁移：安全地添加新列和索引"""
    conn = get_connection()
    c = conn.cursor()
    
    # 添加新列
    migrations = [
        ("ai_analysis", "difficulty", "TEXT"),
        ("ai_analysis", "knowledge_summary", "TEXT"),
        ("ai_analysis", "question_count", "INTEGER"),
        ("gaokao_questions", "category", "TEXT"),
    ]
    for table, column, col_type in migrations:
        try:
            c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}')
            print(f"迁移: {table}.{column} 已添加")
        except sqlite3.OperationalError:
            pass  # 列已存在，忽略
    
    # 创建索引以提高查询性能
    indexes = [
        # 用户表索引
        ("idx_users_username", "users", "username"),
        
        # 试卷表索引
        ("idx_exams_subject", "exams", "subject"),
        ("idx_exams_grade", "exams", "grade"),
        ("idx_exams_exam_type", "exams", "exam_type"),
        ("idx_exams_created_at", "exams", "created_at"),
        ("idx_exams_upload_user", "exams", "upload_user_id"),
        
        # 试卷文件表索引
        ("idx_exam_files_exam_id", "exam_files", "exam_id"),
        
        # 题目表索引
        ("idx_questions_exam_id", "questions", "exam_id"),
        ("idx_questions_type", "questions", "question_type"),
        
        # AI分析表索引
        ("idx_ai_analysis_exam_id", "ai_analysis", "exam_id"),
        ("idx_ai_analysis_type", "ai_analysis", "analysis_type"),
        
        # 错题本表索引
        ("idx_mistake_book_user_id", "mistake_book", "user_id"),
        ("idx_mistake_book_subject", "mistake_book", "subject"),
        ("idx_mistake_book_mastery", "mistake_book", "mastery_level"),
        ("idx_mistake_book_review_date", "mistake_book", "next_review_date"),
        
        # 学习统计表索引
        ("idx_study_stats_user_id", "study_stats", "user_id"),
        ("idx_study_stats_subject", "study_stats", "subject"),
        ("idx_study_stats_date", "study_stats", "exam_date"),
        
        # 练习会话表索引
        ("idx_practice_sessions_user_id", "practice_sessions", "user_id"),
        ("idx_practice_sessions_mistake_id", "practice_sessions", "mistake_id"),
        
        # 练习题目表索引
        ("idx_practice_questions_session_id", "practice_questions", "session_id"),
        
        # 改错记录表索引
        ("idx_correction_records_user_id", "correction_records", "user_id"),
        ("idx_correction_records_mistake_id", "correction_records", "mistake_id"),
        
        # 高考真题表索引
        ("idx_gaokao_questions_subject", "gaokao_questions", "subject"),
        ("idx_gaokao_questions_category", "gaokao_questions", "category"),
        ("idx_gaokao_questions_year", "gaokao_questions", "year"),
        ("idx_gaokao_questions_difficulty", "gaokao_questions", "difficulty"),
        
        # 学习计划表索引
        ("idx_study_plans_user_id", "study_plans", "user_id"),
        ("idx_study_plans_status", "study_plans", "status"),
        
        # 计划任务表索引
        ("idx_plan_tasks_plan_id", "plan_tasks", "plan_id"),
    ]
    
    for idx_name, table, column in indexes:
        try:
            c.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})')
            print(f"索引: {idx_name} 已创建")
        except sqlite3.OperationalError as e:
            # 表可能不存在，忽略错误
            pass
    
    conn.commit()
    conn.close()
    
    # 分析表以更新统计信息
    _analyze_tables()

def _analyze_tables():
    """分析表以更新统计信息，优化查询计划器"""
    conn = get_connection()
    try:
        conn.execute('ANALYZE')
        conn.commit()
        print("数据库统计信息已更新")
    except:
        pass
    finally:
        conn.close()

def init_default_config():
    """初始化默认配置"""
    defaults = [
        ('ai_provider', 'openai', 'AI提供商'),
        ('ai_api_key', '', 'AI API Key'),
        ('ai_model', 'gpt-4', 'AI模型名称'),
        ('ai_base_url', 'https://api.openai.com/v1', 'AI API基础URL'),
        ('storage_type', 'local', '存储类型(local/cloud)'),
        ('cloud_provider', '阿里云OSS', '云存储提供商'),
        ('cloud_endpoint', '', '云存储端点'),
        ('cloud_access_key', '', '云存储AccessKey'),
        ('cloud_secret_key', '', '云存储SecretKey'),
        ('cloud_bucket', '', '云存储Bucket'),
        ('upload_max_size', '50', '最大上传大小(MB)'),
        ('allowed_extensions', 'jpg,jpeg,png,gif,bmp,pdf,doc,docx', '允许的文件类型'),
    ]
    
    conn = get_connection()
    c = conn.cursor()
    for key, value, desc in defaults:
        c.execute('INSERT OR IGNORE INTO config (config_key, config_value, description) VALUES (?,?,?)',
                  (key, value, desc))
    conn.commit()
    conn.close()

# ==================== 配置管理 ====================
def get_config(key, default=None):
    conn = get_connection()
    r = conn.execute('SELECT config_value FROM config WHERE config_key=?', (key,)).fetchone()
    conn.close()
    return r['config_value'] if r else default

def set_config(key, value, description=None):
    conn = get_connection()
    if description:
        conn.execute('''INSERT OR REPLACE INTO config (config_key, config_value, description, updated_at) 
                        VALUES (?,?,?,?)''', (key, value, description, datetime.now().isoformat()))
    else:
        conn.execute('''INSERT OR REPLACE INTO config (config_key, config_value, updated_at) 
                        VALUES (?,?,?)''', (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_configs():
    conn = get_connection()
    r = conn.execute('SELECT * FROM config ORDER BY id').fetchall()
    conn.close()
    return [dict(x) for x in r]

# ==================== 用户管理 ====================
def add_user(username, password, role='student', display_name=None, grade=None, class_name=None):
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    try:
        conn.execute('''INSERT INTO users (username, password, role, display_name, grade, class_name) 
                        VALUES (?,?,?,?,?,?)''',
                     (username, pwd_hash, role, display_name or username, grade, class_name))
        conn.commit()
        return True, 'ok'
    except sqlite3.IntegrityError:
        return False, '用户名已存在'
    finally:
        conn.close()

def verify_user(username, password):
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    r = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username, pwd_hash)).fetchone()
    conn.close()
    return dict(r) if r else None

def get_all_users():
    conn = get_connection()
    r = conn.execute('SELECT id, username, role, display_name, grade, class_name, created_at FROM users ORDER BY id').fetchall()
    conn.close()
    return [dict(x) for x in r]

def get_user_by_id(user_id):
    conn = get_connection()
    r = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

# ==================== 试卷管理 ====================
def add_exam(title, subject, grade=None, exam_type='月考', exam_date=None, 
             total_score=150, description=None, file_path=None, file_type=None, 
             cloud_url=None, upload_user_id=None):
    conn = get_connection()
    conn.execute('''INSERT INTO exams (title, subject, grade, exam_type, exam_date, 
                    total_score, description, file_path, file_type, cloud_url, upload_user_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                 (title, subject, grade, exam_type, exam_date, total_score, 
                  description, file_path, file_type, cloud_url, upload_user_id))
    exam_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return exam_id

def get_exam_by_id(exam_id):
    conn = get_connection()
    r = conn.execute('SELECT * FROM exams WHERE id=?', (exam_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def search_exams(keyword=None, subject=None, grade=None, exam_type=None, 
                 start_date=None, end_date=None, limit=100, page=None, per_page=20):
    conn = get_connection()
    query = 'SELECT * FROM exams WHERE 1=1'
    count_query = 'SELECT COUNT(*) FROM exams WHERE 1=1'
    params = []
    
    if keyword:
        query += ' AND (title LIKE ? OR description LIKE ?)'
        count_query += ' AND (title LIKE ? OR description LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if subject:
        query += ' AND subject=?'
        count_query += ' AND subject=?'
        params.append(subject)
    if grade:
        query += ' AND grade=?'
        count_query += ' AND grade=?'
        params.append(grade)
    if exam_type:
        query += ' AND exam_type=?'
        count_query += ' AND exam_type=?'
        params.append(exam_type)
    if start_date:
        query += ' AND exam_date>=?'
        count_query += ' AND exam_date>=?'
        params.append(start_date)
    if end_date:
        query += ' AND exam_date<=?'
        count_query += ' AND exam_date<=?'
        params.append(end_date)
    
    # 获取总数
    total = conn.execute(count_query, params).fetchone()[0]
    
    # 分页查询
    if page:
        offset = (page - 1) * per_page
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
    else:
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    
    results = [dict(x) for x in r]
    
    # 如果启用了分页，返回分页信息
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
            'next_num': page + 1 if page * per_page < total else None
        }
    
    return results

def get_all_exams(limit=100):
    conn = get_connection()
    r = conn.execute('SELECT * FROM exams ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

def update_exam(exam_id, **kw):
    conn = get_connection()
    s = ', '.join(f'{k}=?' for k in kw)
    conn.execute(f'UPDATE exams SET {s} WHERE id=?', list(kw.values()) + [exam_id])
    conn.commit()
    conn.close()

def delete_exam(exam_id):
    conn = get_connection()
    conn.execute('DELETE FROM exams WHERE id=?', (exam_id,))
    conn.commit()
    conn.close()

# ==================== 文件管理 ====================
def add_exam_file(exam_id, file_name, file_path=None, cloud_url=None, 
                  file_type=None, page_number=1):
    conn = get_connection()
    conn.execute('''INSERT INTO exam_files (exam_id, file_name, file_path, cloud_url, 
                    file_type, page_number) VALUES (?,?,?,?,?,?)''',
                 (exam_id, file_name, file_path, cloud_url, file_type, page_number))
    conn.commit()
    conn.close()

def get_exam_files(exam_id):
    conn = get_connection()
    r = conn.execute('SELECT * FROM exam_files WHERE exam_id=? ORDER BY page_number', 
                     (exam_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

# ==================== 题目管理 ====================
def add_question(exam_id, question_number, question_type='选择题', content=None, 
                 answer=None, score=0, user_answer=None, user_score=None):
    conn = get_connection()
    conn.execute('''INSERT INTO questions (exam_id, question_number, question_type, 
                    content, answer, score, user_answer, user_score)
                    VALUES (?,?,?,?,?,?,?,?)''',
                 (exam_id, question_number, question_type, content, answer, 
                  score, user_answer, user_score))
    conn.commit()
    conn.close()

def get_questions_by_exam(exam_id):
    conn = get_connection()
    r = conn.execute('SELECT * FROM questions WHERE exam_id=? ORDER BY question_number', 
                     (exam_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

# 添加别名
get_questions = get_questions_by_exam

def get_question_by_id(question_id):
    conn = get_connection()
    r = conn.execute('SELECT * FROM questions WHERE id=?', (question_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

# ==================== AI分析 ====================
def add_ai_analysis(exam_id, analysis_type, content, model_name=None, difficulty=None, knowledge_summary=None, question_count=None):
    conn = get_connection()
    conn.execute('''INSERT INTO ai_analysis (exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count)
                    VALUES (?,?,?,?,?,?,?)''', (exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count))
    conn.commit()
    conn.close()

def get_ai_analysis(exam_id, analysis_type=None):
    conn = get_connection()
    if analysis_type:
        r = conn.execute('SELECT * FROM ai_analysis WHERE exam_id=? AND analysis_type=? ORDER BY created_at DESC',
                        (exam_id, analysis_type)).fetchall()
    else:
        r = conn.execute('SELECT * FROM ai_analysis WHERE exam_id=? ORDER BY created_at DESC',
                        (exam_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

def get_latest_ai_analysis(exam_id, analysis_type):
    conn = get_connection()
    r = conn.execute('''SELECT * FROM ai_analysis 
                        WHERE exam_id=? AND analysis_type=? 
                        ORDER BY created_at DESC LIMIT 1''',
                     (exam_id, analysis_type)).fetchone()
    conn.close()
    return dict(r) if r else None

def get_all_ai_analyses(exam_id=None, analysis_type=None, limit=100):
    """获取所有AI分析记录"""
    conn = get_connection()
    query = '''SELECT a.*, e.title as exam_title, e.subject as exam_subject 
               FROM ai_analysis a 
               LEFT JOIN exams e ON a.exam_id = e.id 
               WHERE 1=1'''
    params = []
    
    if exam_id:
        query += ' AND a.exam_id=?'
        params.append(exam_id)
    if analysis_type:
        query += ' AND a.analysis_type=?'
        params.append(analysis_type)
    
    query += ' ORDER BY a.created_at DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def delete_ai_analysis(analysis_id):
    """删除AI分析记录"""
    conn = get_connection()
    conn.execute('DELETE FROM ai_analysis WHERE id=?', (analysis_id,))
    conn.commit()
    conn.close()

# ==================== 错题本 ====================
def add_mistake(user_id, question_id=None, exam_id=None, subject=None, 
                question_type=None, content=None, correct_answer=None, 
                user_answer=None, analysis=None):
    conn = get_connection()
    conn.execute('''INSERT INTO mistake_book (user_id, question_id, exam_id, subject, 
                    question_type, content, correct_answer, user_answer, analysis)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                 (user_id, question_id, exam_id, subject, question_type, 
                  content, correct_answer, user_answer, analysis))
    conn.commit()
    conn.close()

def get_mistakes(user_id, subject=None, mastery_level=None, limit=100):
    conn = get_connection()
    query = 'SELECT * FROM mistake_book WHERE user_id=?'
    params = [user_id]
    
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    if mastery_level is not None:
        query += ' AND mastery_level=?'
        params.append(mastery_level)
    
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def update_mistake(mistake_id, **kw):
    conn = get_connection()
    s = ', '.join(f'{k}=?' for k in kw)
    conn.execute(f'UPDATE mistake_book SET {s} WHERE id=?', list(kw.values()) + [mistake_id])
    conn.commit()
    conn.close()

def get_mistake_by_id(mistake_id):
    """根据ID获取单个错题"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM mistake_book WHERE id=?', (mistake_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

# ==================== 学习统计 ====================
def add_study_stat(user_id, subject, exam_date, score, total_score, rank=None, class_avg=None):
    conn = get_connection()
    conn.execute('''INSERT INTO study_stats (user_id, subject, exam_date, score, total_score, rank, class_avg)
                    VALUES (?,?,?,?,?,?,?)''',
                 (user_id, subject, exam_date, score, total_score, rank, class_avg))
    conn.commit()
    conn.close()

def get_study_stats(user_id, subject=None, limit=50):
    conn = get_connection()
    query = 'SELECT * FROM study_stats WHERE user_id=?'
    params = [user_id]
    
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    
    query += ' ORDER BY exam_date DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def get_subject_stats(user_id):
    conn = get_connection()
    r = conn.execute('''SELECT subject, 
                        COUNT(*) as exam_count,
                        AVG(score/total_score*100) as avg_rate,
                        MAX(score/total_score*100) as max_rate,
                        MIN(score/total_score*100) as min_rate
                        FROM study_stats WHERE user_id=?
                        GROUP BY subject''', (user_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

# ==================== 专项练习 ====================
def create_practice_session(user_id, mistake_id=None, subject=None, practice_type='错题巩固', title=None):
    """创建练习会话"""
    conn = get_connection()
    c = conn.execute('''INSERT INTO practice_sessions (user_id, mistake_id, subject, practice_type, title)
                        VALUES (?,?,?,?,?)''',
                     (user_id, mistake_id, subject, practice_type, title))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def add_practice_question(session_id, question_number, question_type, content, 
                          options=None, correct_answer=None, analysis=None):
    """添加练习题目"""
    conn = get_connection()
    conn.execute('''INSERT INTO practice_questions 
                    (session_id, question_number, question_type, content, options, correct_answer, analysis)
                    VALUES (?,?,?,?,?,?,?)''',
                 (session_id, question_number, question_type, content, options, correct_answer, analysis))
    conn.commit()
    conn.close()

def get_practice_session(session_id):
    """获取练习会话"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM practice_sessions WHERE id=?', (session_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def get_practice_questions(session_id):
    """获取练习题目"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM practice_questions WHERE session_id=? ORDER BY question_number',
                     (session_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

def update_practice_answer(question_id, user_answer, is_correct):
    """更新练习答案"""
    conn = get_connection()
    conn.execute('UPDATE practice_questions SET user_answer=?, is_correct=? WHERE id=?',
                 (user_answer, is_correct, question_id))
    conn.commit()
    conn.close()

def complete_practice_session(session_id, correct_count, total_questions):
    """完成练习会话"""
    score = (correct_count / total_questions * 100) if total_questions > 0 else 0
    conn = get_connection()
    conn.execute('''UPDATE practice_sessions 
                    SET status='已完成', correct_count=?, total_questions=?, score=?, completed_at=CURRENT_TIMESTAMP
                    WHERE id=?''',
                 (correct_count, total_questions, score, session_id))
    conn.commit()
    conn.close()
    return score

def get_user_practice_sessions(user_id, subject=None, status=None, limit=50):
    """获取用户练习记录"""
    conn = get_connection()
    query = 'SELECT * FROM practice_sessions WHERE user_id=?'
    params = [user_id]
    
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    if status:
        query += ' AND status=?'
        params.append(status)
    
    query += ' ORDER BY started_at DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def add_correction_record(user_id, mistake_id, practice_question_id, session_id,
                          original_mistake, user_correction, is_correct=0, teacher_comment=None):
    """添加改错记录"""
    conn = get_connection()
    
    # 检查是否已有改错记录
    existing = conn.execute('''SELECT id, correction_count FROM correction_records 
                               WHERE user_id=? AND mistake_id=? AND practice_question_id=?''',
                            (user_id, mistake_id, practice_question_id)).fetchone()
    
    if existing:
        # 更新现有记录
        conn.execute('''UPDATE correction_records 
                        SET user_correction=?, is_correct=?, teacher_comment=?, 
                            correction_count=correction_count+1, created_at=CURRENT_TIMESTAMP
                        WHERE id=?''',
                     (user_correction, is_correct, teacher_comment, existing['id']))
    else:
        # 创建新记录
        conn.execute('''INSERT INTO correction_records 
                        (user_id, mistake_id, practice_question_id, session_id,
                         original_mistake, user_correction, is_correct, teacher_comment)
                        VALUES (?,?,?,?,?,?,?,?)''',
                     (user_id, mistake_id, practice_question_id, session_id,
                      original_mistake, user_correction, is_correct, teacher_comment))
    
    conn.commit()
    conn.close()

def get_correction_records(user_id, mistake_id=None, limit=50):
    """获取改错记录"""
    conn = get_connection()
    query = '''SELECT cr.*, mb.content as mistake_content, mb.subject
               FROM correction_records cr
               LEFT JOIN mistake_book mb ON cr.mistake_id = mb.id
               WHERE cr.user_id=?'''
    params = [user_id]
    
    if mistake_id:
        query += ' AND cr.mistake_id=?'
        params.append(mistake_id)
    
    query += ' ORDER BY cr.created_at DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def get_mistake_practice_history(mistake_id):
    """获取某道错题的练习历史"""
    conn = get_connection()
    r = conn.execute('''SELECT ps.*, pq.user_answer, pq.is_correct
                        FROM practice_sessions ps
                        JOIN practice_questions pq ON ps.id = pq.session_id
                        WHERE ps.mistake_id=?
                        ORDER BY ps.started_at DESC''',
                     (mistake_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

# ==================== 学习计划 ====================
def add_study_plan(user_id, title, subject, start_date, end_date, plan_type='日常学习', 
                   description=None, daily_goal=None):
    """添加学习计划"""
    conn = get_connection()
    c = conn.execute('''INSERT INTO study_plans 
        (user_id, title, subject, plan_type, description, start_date, end_date, daily_goal)
        VALUES (?,?,?,?,?,?,?,?)''',
        (user_id, title, subject, plan_type, description, start_date, end_date, daily_goal))
    plan_id = c.lastrowid
    conn.commit()
    conn.close()
    return plan_id

def get_study_plans(user_id, status=None, subject=None, limit=50):
    """获取学习计划列表"""
    conn = get_connection()
    query = 'SELECT * FROM study_plans WHERE user_id=?'
    params = [user_id]
    
    if status:
        query += ' AND status=?'
        params.append(status)
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    plans = [dict(x) for x in r]
    
    # 为每个计划添加任务和进度计算
    for plan in plans:
        tasks = get_plan_tasks(plan['id'])
        plan['tasks'] = tasks
        if tasks:
            completed_count = sum(1 for t in tasks if t['completed'])
            plan['progress'] = round(completed_count / len(tasks) * 100, 1)
            # 更新数据库中的进度
            conn = get_connection()
            conn.execute('UPDATE study_plans SET progress=? WHERE id=?', 
                        (plan['progress'], plan['id']))
            conn.commit()
            conn.close()
        else:
            plan['progress'] = 0
        
        # 检查是否过期
        from datetime import date
        plan['is_overdue'] = plan['end_date'] < date.today().isoformat() and plan['status'] != '已完成'
    
    conn.close()
    return plans

def get_study_plan_by_id(plan_id):
    """根据ID获取学习计划"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM study_plans WHERE id=?', (plan_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def update_study_plan(plan_id, **kw):
    """更新学习计划"""
    conn = get_connection()
    s = ', '.join(f'{k}=?' for k in kw)
    conn.execute(f'UPDATE study_plans SET {s} WHERE id=?', list(kw.values()) + [plan_id])
    conn.commit()
    conn.close()

def delete_study_plan(plan_id):
    """删除学习计划"""
    conn = get_connection()
    conn.execute('DELETE FROM plan_tasks WHERE plan_id=?', (plan_id,))
    conn.execute('DELETE FROM study_plans WHERE id=?', (plan_id,))
    conn.commit()
    conn.close()

def add_plan_task(plan_id, content, sort_order=0):
    """添加计划任务"""
    conn = get_connection()
    c = conn.execute('''INSERT INTO plan_tasks (plan_id, content, sort_order)
        VALUES (?,?,?)''', (plan_id, content, sort_order))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_plan_tasks(plan_id):
    """获取计划任务列表"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM plan_tasks WHERE plan_id=? ORDER BY sort_order, id', 
                    (plan_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]

def update_plan_task(task_id, completed=None, content=None):
    """更新计划任务"""
    conn = get_connection()
    if completed is not None:
        conn.execute('UPDATE plan_tasks SET completed=? WHERE id=?', (completed, task_id))
    if content is not None:
        conn.execute('UPDATE plan_tasks SET content=? WHERE id=?', (content, task_id))
    conn.commit()
    conn.close()

def get_plan_task_by_id(task_id):
    """根据ID获取计划任务"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM plan_tasks WHERE id=?', (task_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def get_plan_stats(user_id):
    """获取学习计划统计"""
    conn = get_connection()
    r = conn.execute('''SELECT 
                        COUNT(*) as total_plans,
                        SUM(CASE WHEN status='进行中' THEN 1 ELSE 0 END) as active_plans,
                        SUM(CASE WHEN status='已完成' THEN 1 ELSE 0 END) as completed_plans
                        FROM study_plans WHERE user_id=?''', (user_id,)).fetchone()
    stats = dict(r) if r else {'total_plans': 0, 'active_plans': 0, 'completed_plans': 0}
    
    # 计算完成率
    if stats['total_plans'] > 0:
        stats['completion_rate'] = round(stats['completed_plans'] / stats['total_plans'] * 100, 1)
    else:
        stats['completion_rate'] = 0
    
    conn.close()
    return stats

# ==================== 高考真题 ====================
def add_gaokao_question(subject, content, year=None, region=None, question_number=None,
                        question_type='选择题', options=None, correct_answer=None,
                        analysis=None, knowledge_point=None, difficulty='中等',
                        score=None, source=None, category=None):
    """添加高考真题"""
    conn = get_connection()
    c = conn.execute('''INSERT INTO gaokao_questions 
        (subject, category, year, region, question_number, question_type, content, options,
         correct_answer, analysis, knowledge_point, difficulty, score, source)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (subject, category or '', year, region, question_number, question_type, content, options,
         correct_answer, analysis, knowledge_point, difficulty, score, source))
    question_id = c.lastrowid
    conn.commit()
    conn.close()
    return question_id

def search_gaokao_questions(subject=None, knowledge_point=None, question_type=None,
                            year_from=None, year_to=None, difficulty=None, category=None, limit=10):
    """搜索高考真题（支持知识点模糊匹配）"""
    conn = get_connection()
    query = 'SELECT * FROM gaokao_questions WHERE 1=1'
    params = []
    
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    if category:
        query += ' AND category=?'
        params.append(category)
    if knowledge_point:
        # 支持多个知识点用逗号分隔，任一匹配即可
        keywords = [k.strip() for k in knowledge_point.split(',') if k.strip()]
        if keywords:
            kp_conditions = ' OR '.join(['knowledge_point LIKE ?' for _ in keywords])
            query += f' AND ({kp_conditions})'
            params.extend([f'%{k}%' for k in keywords])
    if question_type:
        query += ' AND question_type=?'
        params.append(question_type)
    if year_from:
        query += ' AND year>=?'
        params.append(year_from)
    if year_to:
        query += ' AND year<=?'
        params.append(year_to)
    if difficulty:
        query += ' AND difficulty=?'
        params.append(difficulty)
    
    query += ' ORDER BY year DESC, id DESC LIMIT ?'
    params.append(limit)
    
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def get_gaokao_question_by_id(question_id):
    """获取单道高考真题"""
    conn = get_connection()
    r = conn.execute('SELECT * FROM gaokao_questions WHERE id=?', (question_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def get_all_gaokao_questions(subject=None, year=None, category=None, question_type=None, difficulty=None, limit=200):
    """获取所有高考真题（管理用）"""
    conn = get_connection()
    query = 'SELECT * FROM gaokao_questions WHERE 1=1'
    params = []
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    if year:
        query += ' AND year=?'
        params.append(year)
    if category:
        query += ' AND category=?'
        params.append(category)
    if question_type:
        query += ' AND question_type=?'
        params.append(question_type)
    if difficulty:
        query += ' AND difficulty=?'
        params.append(difficulty)
    query += ' ORDER BY year DESC, subject, category, question_number LIMIT ?'
    params.append(limit)
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(x) for x in r]

def delete_gaokao_question(question_id):
    """删除高考真题"""
    conn = get_connection()
    conn.execute('DELETE FROM gaokao_questions WHERE id=?', (question_id,))
    conn.commit()
    conn.close()

def get_gaokao_stats():
    """获取高考真题统计"""
    conn = get_connection()
    r = conn.execute('''SELECT subject, COUNT(*) as count, MIN(year) as min_year, MAX(year) as max_year
                        FROM gaokao_questions GROUP BY subject ORDER BY count DESC''').fetchall()
    conn.close()
    return [dict(x) for x in r]

def get_gaokao_category_tree():
    """获取分类树：科目 -> 分类 -> 题型 -> 数量"""
    conn = get_connection()
    r = conn.execute('''SELECT subject, category, question_type, COUNT(*) as count
                        FROM gaokao_questions
                        GROUP BY subject, category, question_type
                        ORDER BY subject, category, question_type''').fetchall()
    conn.close()
    
    tree = {}
    for row in r:
        subj = row['subject']
        cat = row['category'] or '未分类'
        qtype = row['question_type']
        count = row['count']
        
        if subj not in tree:
            tree[subj] = {}
        if cat not in tree[subj]:
            tree[subj][cat] = {}
        tree[subj][cat][qtype] = count
    
    return tree

def get_gaokao_categories(subject=None):
    """获取所有分类名称"""
    conn = get_connection()
    query = 'SELECT DISTINCT category FROM gaokao_questions WHERE category != "" '
    params = []
    if subject:
        query += ' AND subject=?'
        params.append(subject)
    query += ' ORDER BY category'
    r = conn.execute(query, params).fetchall()
    conn.close()
    return [row['category'] for row in r]

def update_gaokao_question(question_id, **kw):
    """更新高考真题"""
    conn = get_connection()
    s = ', '.join(f'{k}=?' for k in kw)
    conn.execute(f'UPDATE gaokao_questions SET {s} WHERE id=?', list(kw.values()) + [question_id])
    conn.commit()
    conn.close()

def batch_update_gaokao_category(question_ids, category):
    """批量更新分类"""
    conn = get_connection()
    for qid in question_ids:
        conn.execute('UPDATE gaokao_questions SET category=? WHERE id=?', (category, qid))
    conn.commit()
    conn.close()

# ==================== 初始化管理员 ====================
def init_default_admin():
    from database import get_config
    if not get_config('admin_initialized'):
        add_user('admin', 'admin123', 'admin', '系统管理员')
        set_config('admin_initialized', '1')

if __name__ == '__main__':
    init_db()
    init_default_admin()
    print("数据库初始化完成")
