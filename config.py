#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责从 gs.env 文件加载配置
"""

import os
import sys

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


def load_config():
    """从 .env 文件加载配置"""
    config = {}
    
    # 加载 .env 文件
    if DOTENV_AVAILABLE:
        env_file = os.path.join(os.path.dirname(__file__), 'gs.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"已加载配置文件: {env_file}")
        else:
            print(f"警告: 配置文件 {env_file} 不存在")
    
    # 从环境变量读取配置
    config['GITEA_URL'] = os.getenv('GITEA_URL')
    config['GITEA_TOKEN'] = os.getenv('GITEA_TOKEN')
    config['GITEA_USERNAME'] = os.getenv('GITEA_USERNAME')
    config['GITEA_PASSWORD'] = os.getenv('GITEA_PASSWORD')
    config['REDIS_HOST'] = os.getenv('REDIS_HOST')
    config['REDIS_PORT'] = os.getenv('REDIS_PORT')
    config['REDIS_DB'] = os.getenv('REDIS_DB')
    config['REDIS_PASSWORD'] = os.getenv('REDIS_PASSWORD')
    config['CLONE_DIR'] = os.getenv('CLONE_DIR')
    config['OUTPUT_PATH'] = os.getenv('OUTPUT_PATH')
    config['OUTPUT_FILE'] = os.getenv('OUTPUT_FILE')
    config['JSON_FILE'] = os.getenv('JSON_FILE')
    config['SINCE_DATE'] = os.getenv('SINCE_DATE')
    config['END_DATE'] = os.getenv('END_DATE')
    config['DAYS'] = os.getenv('DAYS')
    config['PERIOD'] = os.getenv('PERIOD')
    config['USER_ALIASES'] = os.getenv('USER_ALIASES')
    config['iscommit'] = os.getenv('iscommit', 'true')  # 默认为 true
    
    return config


def validate_config(config):
    """验证配置参数"""
    # 验证必需参数
    if not config['GITEA_URL']:
        print("错误: 缺少必需参数 GITEA_URL")
        print("\n请在 gs.env 文件中配置以下参数:")
        print("GITEA_URL=https://git.smartcrec.com")
        print("GITEA_TOKEN=your_token")
        print("GITEA_USERNAME=your_username")
        print("GITEA_PASSWORD=your_password")
        print("REDIS_HOST=10.76.2.121")
        print("REDIS_PORT=20002")
        print("REDIS_DB=6")
        print("REDIS_PASSWORD=BimCloud@654")
        print("OUTPUT_FILE=report.txt")
        print("JSON_FILE=stats.json")
        print("SINCE_DATE=2025-12-01")
        print("DAYS=7")
        print("PERIOD=7")
        sys.exit(1)
    
    # 验证认证方式
    if not config['GITEA_TOKEN'] and not (config['GITEA_USERNAME'] and config['GITEA_PASSWORD']):
        print("错误: 必须提供认证方式")
        print("方式一：设置 GITEA_TOKEN")
        print("方式二：设置 GITEA_USERNAME 和 GITEA_PASSWORD")
        sys.exit(1)
    
    return True
