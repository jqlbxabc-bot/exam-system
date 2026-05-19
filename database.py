#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - 数据库模块（支持 SQLite 和 PostgreSQL）"""

import os
from datetime import datetime

# 检测数据库类型
DATABASE_URL = os.environ.get('DATABASE_URL', '')
USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    # Railway PostgreSQL URL 可能以 postgres:// 开头，需要改成 postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'exam_system.db')

def get_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        import sqlite3
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

def _execute(conn, sql, params=None):
    """执行SQL，自动适配参数占位符"""
    if USE_POSTGRES:
        # PostgreSQL 用 %s
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params or ())
        return cur
    else:
        # SQLite 用 ?，把 %s 替换成 ?
        sqlite_sql = sql.replace('%s', '?')
        cur = conn.execute(sqlite_sql, params or ())
        return cur

def _fetchone(cur):
    """获取一行结果"""
    if USE_POSTGRES:
        row = cur.fetchone()
        return dict(row) if row else None
    else:
        row = cur.fetchone()
        return dict(row) if row else None

def _fetchall(cur):
    """获取所有结果"""
    if USE_POSTGRES:
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    else:
        rows = cur.fetchall()
        return [dict(r) for r in rows]

def _lastrowid(conn, cur, table='id'):
    """获取最后插入的ID"""
    if USE_POSTGRES:
        # PostgreSQL 用 RETURNING
        return cur.fetchone()[table] if cur else None
    else:
        return conn.execute('SELECT last_insert_rowid()').fetchone()[0]

def init_db():
    conn = get_connection()
    
    # 建表语句 - 使用通用SQL语法
    tables = [
        '''CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            role VARCHAR(20) DEFAULT 'student',
            display_name VARCHAR(100),
            grade VARCHAR(20),
            class_name VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS exams (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            subject VARCHAR(50) NOT NULL,
            grade VARCHAR(20),
            exam_type VARCHAR(50) DEFAULT '月考',
            exam_date VARCHAR(20),
            total_score REAL DEFAULT 150,
            description TEXT,
            file_path VARCHAR(500),
            file_type VARCHAR(20),
            cloud_url VARCHAR(500),
            upload_user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS exam_files (
            id SERIAL PRIMARY KEY,
            exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            file_name VARCHAR(200) NOT NULL,
            file_path VARCHAR(500),
            cloud_url VARCHAR(500),
            file_type VARCHAR(20),
            page_number INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            question_number INTEGER,
            question_type VARCHAR(50) DEFAULT '选择题',
            content TEXT,
            answer TEXT,
            score REAL DEFAULT 0,
            user_answer TEXT,
            user_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS ai_analysis (
            id SERIAL PRIMARY KEY,
            exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
            analysis_type VARCHAR(50) DEFAULT '综合分析',
            content TEXT,
            model_name VARCHAR(100),
            difficulty VARCHAR(20),
            knowledge_summary TEXT,
            question_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS mistake_book (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            question_id INTEGER REFERENCES questions(id),
            exam_id INTEGER REFERENCES exams(id),
            subject VARCHAR(50),
            question_type VARCHAR(50),
            content TEXT,
            correct_answer TEXT,
            user_answer TEXT,
            analysis TEXT,
            mastery_level INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            next_review_date VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS study_stats (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            subject VARCHAR(50),
            exam_date VARCHAR(20),
            score REAL,
            total_score REAL,
            rank INTEGER,
            class_avg REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS practice_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            mistake_id INTEGER REFERENCES mistake_book(id),
            subject VARCHAR(50),
            practice_type VARCHAR(50) DEFAULT '错题巩固',
            title VARCHAR(200),
            total_questions INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT '进行中',
            score REAL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''',
        
        '''CREATE TABLE IF NOT EXISTS practice_questions (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
            question_number INTEGER,
            question_type VARCHAR(50) DEFAULT '解答题',
            content TEXT,
            options TEXT,
            correct_answer TEXT,
            user_answer TEXT,
            is_correct INTEGER DEFAULT 0,
            analysis TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS correction_records (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            mistake_id INTEGER REFERENCES mistake_book(id),
            practice_question_id INTEGER REFERENCES practice_questions(id),
            session_id INTEGER REFERENCES practice_sessions(id),
            original_mistake TEXT,
            user_correction TEXT,
            is_correct INTEGER DEFAULT 0,
            teacher_comment TEXT,
            correction_count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS gaokao_questions (
            id SERIAL PRIMARY KEY,
            subject VARCHAR(50) NOT NULL,
            category VARCHAR(100) DEFAULT '',
            year INTEGER,
            region VARCHAR(50),
            question_number INTEGER,
            question_type VARCHAR(50) DEFAULT '选择题',
            content TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT,
            analysis TEXT,
            knowledge_point TEXT,
            difficulty VARCHAR(20) DEFAULT '中等',
            score REAL,
            source VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS study_plans (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title VARCHAR(200) NOT NULL,
            subject VARCHAR(50),
            plan_type VARCHAR(50) DEFAULT '日常学习',
            description TEXT,
            start_date VARCHAR(20) NOT NULL,
            end_date VARCHAR(20) NOT NULL,
            daily_goal TEXT,
            status VARCHAR(20) DEFAULT '进行中',
            progress REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
        
        '''CREATE TABLE IF NOT EXISTS plan_tasks (
            id SERIAL PRIMARY KEY,
            plan_id INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''',
    ]
    
    cur = conn.cursor()
    for sql in tables:
        cur.execute(sql)
    conn.commit()
    conn.close()
    
    # 初始化默认配置
    init_default_config()

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
    for key, value, desc in defaults:
        if USE_POSTGRES:
            _execute(conn, '''INSERT INTO config (config_key, config_value, description, updated_at) 
                             VALUES (%s, %s, %s, %s) ON CONFLICT (config_key) DO NOTHING''',
                    (key, value, desc, datetime.now().isoformat()))
        else:
            _execute(conn, '''INSERT OR IGNORE INTO config (config_key, config_value, description, updated_at) 
                             VALUES (?,?,?,?)''',
                    (key, value, desc, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ==================== 配置管理 ====================
def get_config(key, default=None):
    conn = get_connection()
    cur = _execute(conn, 'SELECT config_value FROM config WHERE config_key=%s', (key,))
    row = _fetchone(cur)
    conn.close()
    return row['config_value'] if row else default

def set_config(key, value, description=None):
    conn = get_connection()
    if USE_POSTGRES:
        if description:
            _execute(conn, '''INSERT INTO config (config_key, config_value, description, updated_at) 
                             VALUES (%s,%s,%s,%s) ON CONFLICT (config_key) DO UPDATE 
                             SET config_value=EXCLUDED.config_value, description=EXCLUDED.description, updated_at=EXCLUDED.updated_at''',
                    (key, value, description, datetime.now().isoformat()))
        else:
            _execute(conn, '''INSERT INTO config (config_key, config_value, updated_at) 
                             VALUES (%s,%s,%s) ON CONFLICT (config_key) DO UPDATE 
                             SET config_value=EXCLUDED.config_value, updated_at=EXCLUDED.updated_at''',
                    (key, value, datetime.now().isoformat()))
    else:
        if description:
            _execute(conn, '''INSERT OR REPLACE INTO config (config_key, config_value, description, updated_at) 
                             VALUES (?,?,?,?)''',
                    (key, value, description, datetime.now().isoformat()))
        else:
            _execute(conn, '''INSERT OR REPLACE INTO config (config_key, config_value, updated_at) 
                             VALUES (?,?,?)''',
                    (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_configs():
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM config ORDER BY id')
    results = _fetchall(cur)
    conn.close()
    return results

# ==================== 用户管理 ====================
def add_user(username, password, role='student', display_name=None, grade=None, class_name=None):
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    try:
        if USE_POSTGRES:
            _execute(conn, '''INSERT INTO users (username, password, role, display_name, grade, class_name) 
                            VALUES (%s,%s,%s,%s,%s,%s)''',
                    (username, pwd_hash, role, display_name or username, grade, class_name))
        else:
            _execute(conn, '''INSERT INTO users (username, password, role, display_name, grade, class_name) 
                            VALUES (?,?,?,?,?,?)''',
                    (username, pwd_hash, role, display_name or username, grade, class_name))
        conn.commit()
        return True, 'ok'
    except Exception as e:
        conn.rollback()
        if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
            return False, '用户名已存在'
        raise
    finally:
        conn.close()

def verify_user(username, password):
    import hashlib
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM users WHERE username=%s AND password=%s', (username, pwd_hash))
    row = _fetchone(cur)
    conn.close()
    return row

def get_all_users():
    conn = get_connection()
    cur = _execute(conn, 'SELECT id, username, role, display_name, grade, class_name, created_at FROM users ORDER BY id')
    results = _fetchall(cur)
    conn.close()
    return results

def get_user_by_id(user_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM users WHERE id=%s', (user_id,))
    row = _fetchone(cur)
    conn.close()
    return row

# ==================== 试卷管理 ====================
def add_exam(title, subject, grade=None, exam_type='月考', exam_date=None, 
             total_score=150, description=None, file_path=None, file_type=None, 
             cloud_url=None, upload_user_id=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO exams (title, subject, grade, exam_type, exam_date, 
                        total_score, description, file_path, file_type, cloud_url, upload_user_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (title, subject, grade, exam_type, exam_date, total_score, 
                 description, file_path, file_type, cloud_url, upload_user_id))
        exam_id = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO exams (title, subject, grade, exam_type, exam_date, 
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
    cur = _execute(conn, 'SELECT * FROM exams WHERE id=%s', (exam_id,))
    row = _fetchone(cur)
    conn.close()
    return row

def search_exams(keyword=None, subject=None, grade=None, exam_type=None, 
                 start_date=None, end_date=None, limit=100, page=None, per_page=20):
    conn = get_connection()
    query = 'SELECT * FROM exams WHERE 1=1'
    count_query = 'SELECT COUNT(*) as cnt FROM exams WHERE 1=1'
    params = []
    
    if keyword:
        query += ' AND (title LIKE %s OR description LIKE %s)'
        count_query += ' AND (title LIKE %s OR description LIKE %s)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if subject:
        query += ' AND subject=%s'
        count_query += ' AND subject=%s'
        params.append(subject)
    if grade:
        query += ' AND grade=%s'
        count_query += ' AND grade=%s'
        params.append(grade)
    if exam_type:
        query += ' AND exam_type=%s'
        count_query += ' AND exam_type=%s'
        params.append(exam_type)
    if start_date:
        query += ' AND exam_date>=%s'
        count_query += ' AND exam_date>=%s'
        params.append(start_date)
    if end_date:
        query += ' AND exam_date<=%s'
        count_query += ' AND exam_date<=%s'
        params.append(end_date)
    
    # 获取总数
    cur = _execute(conn, count_query, params)
    total = _fetchone(cur)['cnt']
    
    # 分页查询
    if page:
        offset = (page - 1) * per_page
        query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
        params.extend([per_page, offset])
    else:
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
    
    cur = _execute(conn, query, params)
    results = _fetchall(cur)
    conn.close()
    
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
            'next_num': page + 1 if page * per_page < total else None,
        }
    return {'items': results, 'total': total}

def update_exam(exam_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(exam_id)
    sql = f'UPDATE exams SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

def delete_exam(exam_id):
    conn = get_connection()
    _execute(conn, 'DELETE FROM exams WHERE id=%s', (exam_id,))
    conn.commit()
    conn.close()

# ==================== 题目管理 ====================
def add_question(exam_id, question_number, question_type='选择题', content=None, 
                 answer=None, score=0, user_answer=None, user_score=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO questions (exam_id, question_number, question_type, content, answer, score, user_answer, user_score)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (exam_id, question_number, question_type, content, answer, score, user_answer, user_score))
        qid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO questions (exam_id, question_number, question_type, content, answer, score, user_answer, user_score)
                        VALUES (?,?,?,?,?,?,?,?)''',
                (exam_id, question_number, question_type, content, answer, score, user_answer, user_score))
        qid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return qid

def get_questions_by_exam(exam_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM questions WHERE exam_id=%s ORDER BY question_number', (exam_id,))
    results = _fetchall(cur)
    conn.close()
    return results

def update_question(question_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(question_id)
    sql = f'UPDATE questions SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

# ==================== AI分析管理 ====================
def add_analysis(exam_id, analysis_type='综合分析', content=None, model_name=None,
                 difficulty=None, knowledge_summary=None, question_count=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO ai_analysis (exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count)
                        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count))
        aid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO ai_analysis (exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count)
                        VALUES (?,?,?,?,?,?,?)''',
                (exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count))
        aid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return aid

def get_analyses_by_exam(exam_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM ai_analysis WHERE exam_id=%s ORDER BY created_at DESC', (exam_id,))
    results = _fetchall(cur)
    conn.close()
    return results

# ==================== 错题本管理 ====================
def add_mistake(user_id, question_id=None, exam_id=None, subject=None, question_type=None,
                content=None, correct_answer=None, user_answer=None, analysis=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO mistake_book (user_id, question_id, exam_id, subject, question_type, content, correct_answer, user_answer, analysis)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (user_id, question_id, exam_id, subject, question_type, content, correct_answer, user_answer, analysis))
        mid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO mistake_book (user_id, question_id, exam_id, subject, question_type, content, correct_answer, user_answer, analysis)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                (user_id, question_id, exam_id, subject, question_type, content, correct_answer, user_answer, analysis))
        mid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return mid

def get_mistakes_by_user(user_id, subject=None, mastery_level=None, limit=100):
    conn = get_connection()
    query = 'SELECT * FROM mistake_book WHERE user_id=%s'
    params = [user_id]
    if subject:
        query += ' AND subject=%s'
        params.append(subject)
    if mastery_level is not None:
        query += ' AND mastery_level=%s'
        params.append(mastery_level)
    query += ' ORDER BY created_at DESC LIMIT %s'
    params.append(limit)
    cur = _execute(conn, query, params)
    results = _fetchall(cur)
    conn.close()
    return results

def update_mistake(mistake_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(mistake_id)
    sql = f'UPDATE mistake_book SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

def delete_mistake(mistake_id):
    conn = get_connection()
    _execute(conn, 'DELETE FROM mistake_book WHERE id=%s', (mistake_id,))
    conn.commit()
    conn.close()

# ==================== 学习统计 ====================
def add_study_stat(user_id, subject=None, exam_date=None, score=None, 
                   total_score=None, rank=None, class_avg=None):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn, '''INSERT INTO study_stats (user_id, subject, exam_date, score, total_score, rank, class_avg)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                (user_id, subject, exam_date, score, total_score, rank, class_avg))
    else:
        _execute(conn, '''INSERT INTO study_stats (user_id, subject, exam_date, score, total_score, rank, class_avg)
                        VALUES (?,?,?,?,?,?,?)''',
                (user_id, subject, exam_date, score, total_score, rank, class_avg))
    conn.commit()
    conn.close()

def get_study_stats(user_id, subject=None, limit=50):
    conn = get_connection()
    query = 'SELECT * FROM study_stats WHERE user_id=%s'
    params = [user_id]
    if subject:
        query += ' AND subject=%s'
        params.append(subject)
    query += ' ORDER BY exam_date DESC LIMIT %s'
    params.append(limit)
    cur = _execute(conn, query, params)
    results = _fetchall(cur)
    conn.close()
    return results

# ==================== 练习管理 ====================
def add_practice_session(user_id, mistake_id=None, subject=None, practice_type='错题巩固', title=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO practice_sessions (user_id, mistake_id, subject, practice_type, title)
                        VALUES (%s,%s,%s,%s,%s) RETURNING id''',
                (user_id, mistake_id, subject, practice_type, title))
        sid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO practice_sessions (user_id, mistake_id, subject, practice_type, title)
                        VALUES (?,?,?,?,?)''',
                (user_id, mistake_id, subject, practice_type, title))
        sid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return sid

def get_practice_session(session_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM practice_sessions WHERE id=%s', (session_id,))
    row = _fetchone(cur)
    conn.close()
    return row

def update_practice_session(session_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(session_id)
    sql = f'UPDATE practice_sessions SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

def get_practice_sessions_by_user(user_id, subject=None, status=None, limit=50):
    conn = get_connection()
    query = 'SELECT * FROM practice_sessions WHERE user_id=%s'
    params = [user_id]
    if subject:
        query += ' AND subject=%s'
        params.append(subject)
    if status:
        query += ' AND status=%s'
        params.append(status)
    query += ' ORDER BY started_at DESC LIMIT %s'
    params.append(limit)
    cur = _execute(conn, query, params)
    results = _fetchall(cur)
    conn.close()
    return results

# ==================== 练习题目 ====================
def add_practice_question(session_id, question_number=None, question_type='解答题',
                          content=None, options=None, correct_answer=None, user_answer=None,
                          is_correct=0, analysis=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO practice_questions (session_id, question_number, question_type, content, options, correct_answer, user_answer, is_correct, analysis)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (session_id, question_number, question_type, content, options, correct_answer, user_answer, is_correct, analysis))
        qid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO practice_questions (session_id, question_number, question_type, content, options, correct_answer, user_answer, is_correct, analysis)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                (session_id, question_number, question_type, content, options, correct_answer, user_answer, is_correct, analysis))
        qid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return qid

def get_practice_questions(session_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM practice_questions WHERE session_id=%s ORDER BY question_number', (session_id,))
    results = _fetchall(cur)
    conn.close()
    return results

# ==================== 改错记录 ====================
def add_correction(user_id, mistake_id=None, practice_question_id=None, session_id=None,
                   original_mistake=None, user_correction=None, is_correct=0, teacher_comment=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO correction_records (user_id, mistake_id, practice_question_id, session_id, original_mistake, user_correction, is_correct, teacher_comment)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (user_id, mistake_id, practice_question_id, session_id, original_mistake, user_correction, is_correct, teacher_comment))
        cid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO correction_records (user_id, mistake_id, practice_question_id, session_id, original_mistake, user_correction, is_correct, teacher_comment)
                        VALUES (?,?,?,?,?,?,?,?)''',
                (user_id, mistake_id, practice_question_id, session_id, original_mistake, user_correction, is_correct, teacher_comment))
        cid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return cid

def get_corrections_by_user(user_id, limit=100):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM correction_records WHERE user_id=%s ORDER BY created_at DESC LIMIT %s', (user_id, limit))
    results = _fetchall(cur)
    conn.close()
    return results

# ==================== 高考真题 ====================
def add_gaokao_question(subject, content, category='', year=None, region=None,
                       question_number=None, question_type='选择题', options=None,
                       correct_answer=None, analysis=None, knowledge_point=None,
                       difficulty='中等', score=None, source=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO gaokao_questions (subject, category, year, region, question_number, question_type, content, options, correct_answer, analysis, knowledge_point, difficulty, score, source)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (subject, category, year, region, question_number, question_type, content, options, correct_answer, analysis, knowledge_point, difficulty, score, source))
        qid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO gaokao_questions (subject, category, year, region, question_number, question_type, content, options, correct_answer, analysis, knowledge_point, difficulty, score, source)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (subject, category, year, region, question_number, question_type, content, options, correct_answer, analysis, knowledge_point, difficulty, score, source))
        qid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return qid

def search_gaokao_questions(subject=None, category=None, year=None, difficulty=None,
                           keyword=None, limit=100, page=None, per_page=20):
    conn = get_connection()
    query = 'SELECT * FROM gaokao_questions WHERE 1=1'
    count_query = 'SELECT COUNT(*) as cnt FROM gaokao_questions WHERE 1=1'
    params = []
    
    if subject:
        query += ' AND subject=%s'
        count_query += ' AND subject=%s'
        params.append(subject)
    if category:
        query += ' AND category=%s'
        count_query += ' AND category=%s'
        params.append(category)
    if year:
        query += ' AND year=%s'
        count_query += ' AND year=%s'
        params.append(year)
    if difficulty:
        query += ' AND difficulty=%s'
        count_query += ' AND difficulty=%s'
        params.append(difficulty)
    if keyword:
        query += ' AND (content LIKE %s OR knowledge_point LIKE %s)'
        count_query += ' AND (content LIKE %s OR knowledge_point LIKE %s)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    
    cur = _execute(conn, count_query, params)
    total = _fetchone(cur)['cnt']
    
    if page:
        offset = (page - 1) * per_page
        query += ' ORDER BY created_at DESC LIMIT %s OFFSET %s'
        params.extend([per_page, offset])
    else:
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
    
    cur = _execute(conn, query, params)
    results = _fetchall(cur)
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

# ==================== 学习计划 ====================
def add_study_plan(user_id, title, subject=None, plan_type='日常学习', description=None,
                   start_date=None, end_date=None, daily_goal=None):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO study_plans (user_id, title, subject, plan_type, description, start_date, end_date, daily_goal)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id''',
                (user_id, title, subject, plan_type, description, start_date, end_date, daily_goal))
        pid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO study_plans (user_id, title, subject, plan_type, description, start_date, end_date, daily_goal)
                        VALUES (?,?,?,?,?,?,?,?)''',
                (user_id, title, subject, plan_type, description, start_date, end_date, daily_goal))
        pid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return pid

def get_study_plans(user_id, status=None):
    conn = get_connection()
    query = 'SELECT * FROM study_plans WHERE user_id=%s'
    params = [user_id]
    if status:
        query += ' AND status=%s'
        params.append(status)
    query += ' ORDER BY created_at DESC'
    cur = _execute(conn, query, params)
    results = _fetchall(cur)
    conn.close()
    return results

def update_study_plan(plan_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(plan_id)
    sql = f'UPDATE study_plans SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

# ==================== 计划任务 ====================
def add_plan_task(plan_id, content, sort_order=0):
    conn = get_connection()
    if USE_POSTGRES:
        _execute(conn, '''INSERT INTO plan_tasks (plan_id, content, sort_order) VALUES (%s,%s,%s)''',
                (plan_id, content, sort_order))
    else:
        _execute(conn, '''INSERT INTO plan_tasks (plan_id, content, sort_order) VALUES (?,?,?)''',
                (plan_id, content, sort_order))
    conn.commit()
    conn.close()

def get_plan_tasks(plan_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM plan_tasks WHERE plan_id=%s ORDER BY sort_order', (plan_id,))
    results = _fetchall(cur)
    conn.close()
    return results

def update_plan_task(task_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(task_id)
    sql = f'UPDATE plan_tasks SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

# ==================== 文件记录 ====================
def add_exam_file(exam_id, file_name, file_path=None, cloud_url=None, file_type=None, page_number=1):
    conn = get_connection()
    if USE_POSTGRES:
        cur = _execute(conn, '''INSERT INTO exam_files (exam_id, file_name, file_path, cloud_url, file_type, page_number)
                        VALUES (%s,%s,%s,%s,%s,%s) RETURNING id''',
                (exam_id, file_name, file_path, cloud_url, file_type, page_number))
        fid = cur.fetchone()['id']
    else:
        _execute(conn, '''INSERT INTO exam_files (exam_id, file_name, file_path, cloud_url, file_type, page_number)
                        VALUES (?,?,?,?,?,?)''',
                (exam_id, file_name, file_path, cloud_url, file_type, page_number))
        fid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    conn.close()
    return fid

def get_exam_files(exam_id):
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM exam_files WHERE exam_id=%s ORDER BY page_number', (exam_id,))
    results = _fetchall(cur)
    conn.close()
    return results

def delete_exam_file(file_id):
    conn = get_connection()
    _execute(conn, 'DELETE FROM exam_files WHERE id=%s', (file_id,))
    conn.commit()
    conn.close()

# ==================== 统计函数 ====================
def get_user_stats_summary(user_id):
    """获取用户学习统计摘要"""
    conn = get_connection()
    
    # 错题数量
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM mistake_book WHERE user_id=%s', (user_id,))
    mistake_count = _fetchone(cur)['cnt']
    
    # 已掌握数量
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM mistake_book WHERE user_id=%s AND mastery_level>=3', (user_id,))
    mastered_count = _fetchone(cur)['cnt']
    
    # 练习次数
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM practice_sessions WHERE user_id=%s', (user_id,))
    practice_count = _fetchone(cur)['cnt']
    
    # 各科错题分布
    cur = _execute(conn, '''SELECT subject, COUNT(*) as cnt FROM mistake_book 
                           WHERE user_id=%s AND subject IS NOT NULL 
                           GROUP BY subject ORDER BY cnt DESC''', (user_id,))
    subject_stats = _fetchall(cur)
    
    conn.close()
    
    return {
        'mistake_count': mistake_count,
        'mastered_count': mastered_count,
        'practice_count': practice_count,
        'subject_stats': subject_stats,
    }

def get_dashboard_stats():
    """获取仪表板统计"""
    conn = get_connection()
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM exams')
    exam_count = _fetchone(cur)['cnt']
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM users')
    user_count = _fetchone(cur)['cnt']
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM questions')
    question_count = _fetchone(cur)['cnt']
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM mistake_book')
    mistake_count = _fetchone(cur)['cnt']
    
    conn.close()
    
    return {
        'exam_count': exam_count,
        'user_count': user_count,
        'question_count': question_count,
        'mistake_count': mistake_count,
    }

# ==================== 兼容旧代码 ====================
def init_default_admin():
    """初始化默认管理员"""
    try:
        result = add_user('admin', 'admin123', 'admin', '系统管理员')
        if result[0]:
            print("默认管理员已创建: admin/admin123")
        else:
            print("管理员已存在")
    except Exception as e:
        print(f"初始化管理员失败: {e}")

# 为了兼容旧代码中的 import
def get_config_safe(key, default=None):
    try:
        return get_config(key, default)
    except:
        return default

# ==================== 补充缺失的函数 ====================

def get_all_exams(limit=100):
    """获取所有试卷"""
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM exams ORDER BY created_at DESC LIMIT %s', (limit,))
    results = _fetchall(cur)
    conn.close()
    return results

def get_mistakes(user_id, subject=None, limit=100):
    """获取错题列表（兼容旧接口）"""
    return get_mistakes_by_user(user_id, subject=subject, limit=limit)

def get_questions(exam_id):
    """获取试卷题目（兼容旧接口）"""
    return get_questions_by_exam(exam_id)

def add_ai_analysis(exam_id, analysis_type='综合分析', content=None, model_name=None,
                    difficulty=None, knowledge_summary=None, question_count=None):
    """添加AI分析（兼容旧接口）"""
    return add_analysis(exam_id, analysis_type, content, model_name, difficulty, knowledge_summary, question_count)

def get_ai_analysis(analysis_id):
    """获取单个AI分析"""
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM ai_analysis WHERE id=%s', (analysis_id,))
    row = _fetchone(cur)
    conn.close()
    return row

def get_all_ai_analyses(exam_id=None, limit=100):
    """获取所有AI分析"""
    conn = get_connection()
    if exam_id:
        cur = _execute(conn, 'SELECT * FROM ai_analysis WHERE exam_id=%s ORDER BY created_at DESC LIMIT %s', (exam_id, limit))
    else:
        cur = _execute(conn, 'SELECT * FROM ai_analysis ORDER BY created_at DESC LIMIT %s', (limit,))
    results = _fetchall(cur)
    conn.close()
    return results

def get_latest_ai_analysis(exam_id, analysis_type=None):
    """获取最新的AI分析"""
    conn = get_connection()
    if analysis_type:
        cur = _execute(conn, 'SELECT * FROM ai_analysis WHERE exam_id=%s AND analysis_type=%s ORDER BY created_at DESC LIMIT 1', (exam_id, analysis_type))
    else:
        cur = _execute(conn, 'SELECT * FROM ai_analysis WHERE exam_id=%s ORDER BY created_at DESC LIMIT 1', (exam_id,))
    row = _fetchone(cur)
    conn.close()
    return row

def delete_ai_analysis(analysis_id):
    """删除AI分析"""
    conn = get_connection()
    _execute(conn, 'DELETE FROM ai_analysis WHERE id=%s', (analysis_id,))
    conn.commit()
    conn.close()

def add_correction_record(user_id, mistake_id=None, practice_question_id=None, session_id=None,
                          original_mistake=None, user_correction=None, is_correct=0, teacher_comment=None):
    """添加改错记录（兼容旧接口）"""
    return add_correction(user_id, mistake_id, practice_question_id, session_id, 
                         original_mistake, user_correction, is_correct, teacher_comment)

def get_correction_records(user_id, limit=100):
    """获取改错记录（兼容旧接口）"""
    return get_corrections_by_user(user_id, limit)

def get_mistake_by_id(mistake_id):
    """获取单个错题"""
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM mistake_book WHERE id=%s', (mistake_id,))
    row = _fetchone(cur)
    conn.close()
    return row

def create_practice_session(user_id, mistake_id=None, subject=None, practice_type='错题巩固', title=None):
    """创建练习会话（兼容旧接口）"""
    return add_practice_session(user_id, mistake_id, subject, practice_type, title)

def complete_practice_session(session_id, **kwargs):
    """完成练习会话（兼容旧接口）"""
    kwargs['status'] = '已完成'
    kwargs['completed_at'] = datetime.now().isoformat()
    return update_practice_session(session_id, **kwargs)

def update_practice_answer(question_id, user_answer=None, is_correct=0):
    """更新练习答案"""
    conn = get_connection()
    _execute(conn, 'UPDATE practice_questions SET user_answer=%s, is_correct=%s WHERE id=%s',
            (user_answer, is_correct, question_id))
    conn.commit()
    conn.close()

def get_user_practice_sessions(user_id, subject=None, status=None, limit=50):
    """获取用户练习会话（兼容旧接口）"""
    return get_practice_sessions_by_user(user_id, subject, status, limit)

def get_all_gaokao_questions(limit=100):
    """获取所有高考真题"""
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM gaokao_questions ORDER BY created_at DESC LIMIT %s', (limit,))
    results = _fetchall(cur)
    conn.close()
    return results

def get_gaokao_question_by_id(question_id):
    """获取单个高考真题"""
    conn = get_connection()
    cur = _execute(conn, 'SELECT * FROM gaokao_questions WHERE id=%s', (question_id,))
    row = _fetchone(cur)
    conn.close()
    return row

def update_gaokao_question(question_id, **kwargs):
    """更新高考真题"""
    conn = get_connection()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f'{key}=%s')
        values.append(value)
    values.append(question_id)
    sql = f'UPDATE gaokao_questions SET {", ".join(fields)} WHERE id=%s'
    _execute(conn, sql, values)
    conn.commit()
    conn.close()

def delete_gaokao_question(question_id):
    """删除高考真题"""
    conn = get_connection()
    _execute(conn, 'DELETE FROM gaokao_questions WHERE id=%s', (question_id,))
    conn.commit()
    conn.close()

def get_gaokao_category_tree():
    """获取高考真题分类树"""
    conn = get_connection()
    cur = _execute(conn, '''SELECT DISTINCT subject, category, COUNT(*) as cnt 
                           FROM gaokao_questions 
                           WHERE category != '' 
                           GROUP BY subject, category 
                           ORDER BY subject, category''')
    results = _fetchall(cur)
    conn.close()
    
    tree = {}
    for r in results:
        subject = r['subject']
        if subject not in tree:
            tree[subject] = []
        tree[subject].append({'category': r['category'], 'count': r['cnt']})
    return tree

def get_gaokao_stats():
    """获取高考真题统计"""
    conn = get_connection()
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM gaokao_questions')
    total = _fetchone(cur)['cnt']
    
    cur = _execute(conn, 'SELECT subject, COUNT(*) as cnt FROM gaokao_questions GROUP BY subject ORDER BY cnt DESC')
    by_subject = _fetchall(cur)
    
    cur = _execute(conn, 'SELECT year, COUNT(*) as cnt FROM gaokao_questions WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC')
    by_year = _fetchall(cur)
    
    conn.close()
    return {'total': total, 'by_subject': by_subject, 'by_year': by_year}

def delete_study_plan(plan_id):
    """删除学习计划"""
    conn = get_connection()
    _execute(conn, 'DELETE FROM study_plans WHERE id=%s', (plan_id,))
    conn.commit()
    conn.close()

def get_plan_stats(user_id):
    """获取学习计划统计"""
    conn = get_connection()
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM study_plans WHERE user_id=%s', (user_id,))
    total = _fetchone(cur)['cnt']
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM study_plans WHERE user_id=%s AND status=%s', (user_id, '进行中'))
    in_progress = _fetchone(cur)['cnt']
    
    cur = _execute(conn, 'SELECT COUNT(*) as cnt FROM study_plans WHERE user_id=%s AND status=%s', (user_id, '已完成'))
    completed = _fetchone(cur)['cnt']
    
    conn.close()
    return {'total': total, 'in_progress': in_progress, 'completed': completed}

def get_subject_stats(user_id):
    """获取科目统计"""
    conn = get_connection()
    
    cur = _execute(conn, '''SELECT subject, COUNT(*) as cnt, 
                           AVG(CASE WHEN mastery_level >= 3 THEN 1.0 ELSE 0.0 END) * 100 as mastery_rate
                           FROM mistake_book 
                           WHERE user_id=%s AND subject IS NOT NULL 
                           GROUP BY subject ORDER BY cnt DESC''', (user_id,))
    results = _fetchall(cur)
    conn.close()
    return results
