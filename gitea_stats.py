#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gitea 所有项目所有人员代码贡献度统计工具
通过 Gitea API 获取所有仓库的提交统计信息
支持 API Token 和用户名密码两种认证方式
支持按时间范围统计：近一周、近两周、近一个月
排除 fork 的仓库和 fork/ 开头的仓库
优化：只统计规定时间内有变动的仓库
优化：只统计 Gitea 中现有账户的提交，排除外部提交者
优化：跳过 unknown 用户，确保提交时间在指定范围内
优化：统计代码行数（新增行数 + 删除行数）
优化：使用 Redis 缓存提高性能
优化：使用 Git 命令直接查询，避免分页
优化：从 .env 文件读取配置
优化：模块化设计，便于维护和调试
"""

import sys
import os
import shutil
from datetime import datetime, timedelta, timezone

from config import load_config, validate_config
from stats_collector import StatsCollector
from report_generator import ReportGenerator


def process_date_range(config):
    """处理时间范围参数"""
    since_date = None
    until_date = None
    
    # 优先使用 DAYS 参数
    days = None
    if config['DAYS']:
        days = int(config['DAYS'])
    elif config['PERIOD']:
        period = config['PERIOD']
        if period == '7':
            days = 7
        elif period == '14':
            days = 14
        elif period == '30':
            days = 30
    
    if days:
        if days == 1:
            # 当 DAYS=1 时，从前一天的 17:30 开始到当天的 17:30 结束
            now = datetime.now(timezone.utc)
            since_date = (now - timedelta(days=1)).replace(hour=17, minute=30, second=0, microsecond=0).isoformat()
            until_date = now.replace(hour=17, minute=30, second=0, microsecond=0).isoformat()
        else:
            # 当 DAYS>1 时，从当前时间减去 N 天
            since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    elif config['SINCE_DATE']:
        try:
            since_dt = datetime.strptime(config['SINCE_DATE'], '%Y-%m-%d %H:%M:%S')
            since_date = since_dt.isoformat()
        except ValueError:
            print(f"错误：起始日期格式不正确，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    if config['END_DATE'] and not days:
        try:
            until_dt = datetime.strptime(config['END_DATE'], '%Y-%m-%d %H:%M:%S')
            until_date = until_dt.isoformat()
        except ValueError:
            print(f"错误：结束日期格式不正确，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    return since_date, until_date


def main():
    """主函数"""
    print("=" * 80)
    print("Gitea 代码贡献度统计工具")
    print("=" * 80)
    print()
    
    # 加载配置
    config = load_config()
    
    # 验证配置
    validate_config(config)
    
    # 处理时间范围参数
    since_date, until_date = process_date_range(config)
    
    # 创建统计收集器
    collector = StatsCollector(config)
    
    # 清理所有提交记录的缓存
    if collector.redis_cache and collector.redis_cache.enabled:
        collector.redis_cache.delete_pattern('gitea:commits:*')
        print("已清理所有提交记录缓存")
    
    # 收集统计数据
    stats = collector.collect_all_stats(since_date=since_date, until_date=until_date)
    
    # 创建报告生成器
    report_generator = ReportGenerator(collector.gitea_users)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    output_file = config['OUTPUT_FILE']
    if output_file:
        output_file = output_file.replace('.md', '').replace('.txt', '')
        output_file = f"{output_file}_{timestamp}.md"
    
    # 确定输出路径
    output_path = config.get('OUTPUT_PATH', '')
    if output_path:
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)
            print(f"创建输出目录: {output_path}")
        output_file = os.path.join(output_path, output_file)
    
    # 生成报告
    report = report_generator.generate_text_report(stats, output_file, since_date, until_date)
    print("\n" + report)
    
    # 导出 JSON
    json_file = config['JSON_FILE']
    if json_file:
        if output_path:
            json_file = os.path.join(output_path, json_file)
        report_generator.export_json(stats, json_file)
    
    # 复制报告到指定目录（仅在 iscommit 为 true 时执行）
    if config.get('iscommit', 'true').lower() == 'true':
        target_report_dir = '/home/gitea/clone/doc/w01.k8s/docker/gitea/report'
        if not os.path.exists(target_report_dir):
            os.makedirs(target_report_dir, exist_ok=True)
            print(f"创建目标目录: {target_report_dir}")
        
        # 复制 Markdown 报告
        if output_path:
            source_md_file = output_file
            target_md_file = os.path.join(target_report_dir, os.path.basename(output_file))
            shutil.copy(source_md_file, target_md_file)
            print(f"复制 Markdown 报告到: {target_md_file}")
        
        # 复制 JSON 报告
        if json_file:
            if output_path:
                source_json_file = json_file
                target_json_file = os.path.join(target_report_dir, os.path.basename(json_file))
                shutil.copy(source_json_file, target_json_file)
                print(f"复制 JSON 报告到: {target_json_file}")
        
        # Git 提交和推送
        try:
            import subprocess
            
            # 进入目标目录
            os.chdir(target_report_dir)
            
            # 添加所有文件
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True, text=True)
            
            # 提交
            commit_message = f"更新代码贡献度统计报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True, text=True)
            
            # 推送
            subprocess.run(['git', 'push'], check=True, capture_output=True, text=True)
            
            print(f"已提交并推送到 Gitea: {target_report_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Git 操作失败: {e}")
            print(f"错误输出: {e.stderr}")
        except Exception as e:
            print(f"发生错误: {e}")
    else:
        print("\niscommit=false，跳过复制报告和 Git 提交推送操作")
    
    print("\n统计完成！")


if __name__ == '__main__':
    main()
