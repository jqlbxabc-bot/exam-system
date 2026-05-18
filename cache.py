#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""试卷管理系统 - 缓存模块"""

import time
from functools import wraps
from threading import Lock

class SimpleCache:
    """简单的内存缓存"""
    
    def __init__(self, default_timeout=300):
        """
        初始化缓存
        :param default_timeout: 默认缓存时间（秒），默认5分钟
        """
        self._cache = {}
        self._lock = Lock()
        self.default_timeout = default_timeout
    
    def get(self, key):
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires'] > time.time():
                    return item['value']
                else:
                    # 过期删除
                    del self._cache[key]
            return None
    
    def set(self, key, value, timeout=None):
        """设置缓存值"""
        if timeout is None:
            timeout = self.default_timeout
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires': time.time() + timeout
            }
    
    def delete(self, key):
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def has(self, key):
        """检查缓存是否存在"""
        return self.get(key) is not None
    
    def get_or_set(self, key, func, timeout=None):
        """获取缓存值，如果不存在则调用函数计算并缓存"""
        value = self.get(key)
        if value is None:
            value = func()
            self.set(key, value, timeout)
        return value
    
    def cleanup(self):
        """清理过期缓存"""
        with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._cache.items() if v['expires'] <= now]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def stats(self):
        """获取缓存统计"""
        with self._lock:
            now = time.time()
            total = len(self._cache)
            expired = sum(1 for v in self._cache.values() if v['expires'] <= now)
            return {
                'total': total,
                'active': total - expired,
                'expired': expired
            }

# 全局缓存实例
cache = SimpleCache(default_timeout=300)

def cached(timeout=None, key_prefix=''):
    """
    缓存装饰器
    :param timeout: 缓存时间（秒）
    :param key_prefix: 缓存键前缀
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试获取缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern=None):
    """
    使缓存失效
    :param pattern: 缓存键模式（前缀匹配）
    """
    if pattern is None:
        cache.clear()
    else:
        with cache._lock:
            keys_to_delete = [k for k in cache._cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del cache._cache[key]

# 缓存键常量
CACHE_KEYS = {
    'EXAM_LIST': 'exams:list',
    'EXAM_DETAIL': 'exams:detail',
    'MISTAKE_LIST': 'mistakes:list',
    'STUDY_STATS': 'stats:study',
    'SUBJECT_STATS': 'stats:subject',
    'PLAN_LIST': 'plans:list',
    'PLAN_STATS': 'plans:stats',
    'GAOKAO_LIST': 'gaokao:list',
}
