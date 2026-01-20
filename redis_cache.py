#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 缓存模块
负责 Redis 缓存的读取和写入
"""

import json

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisCache:
    """Redis 缓存管理类"""
    
    def __init__(self, host, port, db, password):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client = None
        self.enabled = False
        
        if REDIS_AVAILABLE and host:
            self._connect()
    
    def _connect(self):
        """连接 Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            self.client.ping()
            self.enabled = True
            print(f"Redis 缓存已启用: {self.host}:{self.port}")
        except Exception as e:
            print(f"Redis 连接失败: {e}，将不使用缓存")
            self.enabled = False
    
    def get(self, key, default=None):
        """从缓存获取数据"""
        if not self.enabled:
            return default
        try:
            value = self.client.get(key)
            return json.loads(value) if value else default
        except Exception as e:
            print(f"缓存读取失败: {e}")
            return default
    
    def set(self, key, value, expire_seconds=3600):
        """设置缓存"""
        if not self.enabled:
            return
        try:
            self.client.setex(key, expire_seconds, json.dumps(value))
        except Exception as e:
            print(f"缓存写入失败: {e}")
    
    def delete(self, key):
        """删除缓存"""
        if not self.enabled:
            return
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"缓存删除失败: {e}")
    
    def clear_all(self):
        """清空所有缓存"""
        if not self.enabled:
            return
        try:
            self.client.flushdb()
            print("所有缓存已清空")
        except Exception as e:
            print(f"清空缓存失败: {e}")
    
    def delete_pattern(self, pattern):
        """删除所有匹配模式的缓存"""
        if not self.enabled:
            return
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                print(f"已删除 {len(keys)} 个匹配 '{pattern}' 的缓存")
        except Exception as e:
            print(f"删除缓存失败: {e}")
