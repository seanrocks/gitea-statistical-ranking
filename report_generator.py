#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成模块
负责生成文本和 JSON 格式的统计报告
"""

import json
from datetime import datetime


class ReportGenerator:
    """报告生成类"""
    
    def __init__(self, gitea_users):
        self.gitea_users = gitea_users
    
    def generate_text_report(self, stats, output_file=None, since_date=None, until_date=None):
        """生成文本格式的统计报告"""
        report = []
        report.append("-" * 80)
        report.append("Gitea 代码贡献度统计报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if since_date and until_date:
            since_str = since_date.split('T')[0] if 'T' in since_date else since_date
            until_str = until_date.split('T')[0] if 'T' in until_date else until_date
            
            # 添加时间部分，精确到分钟
            if 'T' in since_date:
                since_time = since_date.split('T')[1][:5]  # 取 HH:MM
                since_str = f"{since_str} {since_time}"
            
            if 'T' in until_date:
                until_time = until_date.split('T')[1][:5]  # 取 HH:MM
                until_str = f"{until_str} {until_time}"
            
            report.append(f"统计时间: {since_str} 至 {until_str}")
        elif since_date:
            since_str = since_date.split('T')[0] if 'T' in since_date else since_date
            
            # 添加时间部分，精确到分钟
            if 'T' in since_date:
                since_time = since_date.split('T')[1][:5]  # 取 HH:MM
                since_str = f"{since_str} {since_time}"
            
            report.append(f"统计时间: {since_str} 至今")
        elif until_date:
            until_str = until_date.split('T')[0] if 'T' in until_date else until_date
            
            # 添加时间部分，精确到分钟
            if 'T' in until_date:
                until_time = until_date.split('T')[1][:5]  # 取 HH:MM
                until_str = f"{until_str} {until_time}"
            
            report.append(f"统计时间: 至 {until_str}")
        
        report.append("-" * 80)
        report.append("")
        
        report.append("📊 总体统计")
        report.append("-" * 80)
        report.append(f"总仓库数: {stats['total_repos']}")
        report.append(f"总提交数: {stats['total_commits']}")
        report.append(f"总新增行数: {stats['total_additions']:,}")
        report.append(f"总删除行数: {stats['total_deletions']:,}")
        report.append(f"总代码行数: {stats['total_lines']:,}")
        report.append(f"总贡献人数: {len(stats['user_stats'])}")
        report.append(f"Gitea 用户数: {len(self.gitea_users)}")
        report.append("")
        
        report.append("👥 用户贡献排行 (按代码行数)")
        report.append("-" * 80)
        
        # 合并所有用户，包括没有提交记录的用户
        all_users = {}
        for username in self.gitea_users:
            if username in stats['user_stats']:
                all_users[username] = stats['user_stats'][username]
            else:
                all_users[username] = {
                    'total_lines': 0,
                    'additions': 0,
                    'deletions': 0,
                    'commits': 0,
                    'repos_count': 0
                }
        
        sorted_users = sorted(
            all_users.items(),
            key=lambda x: x[1]['total_lines'],
            reverse=True
        )
        
        report.append("| 排名 | 用户名 | 真实姓名 | 代码行数 | 新增 | 删除 | 提交数 | 仓库数 | 贡献度 |")
        report.append("|------|--------|----------|----------|------|------|--------|--------|--------|")
        
        for idx, (username, user_data) in enumerate(sorted_users[:20], 1):
            contribution_rate = user_data['total_lines'] / user_data['commits'] if user_data['commits'] > 0 else 0
            user_info = self.gitea_users.get(username, {})
            if isinstance(user_info, dict):
                real_name = user_info.get('full_name', '')
            else:
                real_name = ''
            report.append(f"| {idx:2d} | {username:30s} | {real_name:10s} | {user_data['total_lines']:10,} | {user_data['additions']:7,} | {user_data['deletions']:7,} | {user_data['commits']:4d} | {user_data['repos_count']:3d} | {contribution_rate:.1f} |")
        
        report.append("")
        
        report.append("📁 仓库活跃度排行 (按代码行数)")
        report.append("-" * 80)
        
        sorted_repos = sorted(
            stats['repo_stats'],
            key=lambda x: x['total_lines'],
            reverse=True
        )
        
        report.append("| 排名 | 仓库 | 代码行数 | 新增 | 删除 | 提交数 | 贡献者数 | 贡献者 |")
        report.append("|------|--------|----------|------|------|--------|----------|--------|")
        
        for idx, repo in enumerate(sorted_repos, 1):
            contributors_with_names = []
            for contributor in repo['contributors'][:10]:
                user_info = self.gitea_users.get(contributor, {})
                if isinstance(user_info, dict):
                    real_name = user_info.get('full_name', '')
                else:
                    real_name = contributor
                contributors_with_names.append(real_name if real_name else contributor)
            
            contributors_str = ', '.join(contributors_with_names)
            if len(repo['contributors']) > 10:
                contributors_str += f" ... (+{len(repo['contributors']) - 10})"
            
            description = repo.get('description', '')
            if description:
                repo_display = description
            else:
                repo_display = repo['name']
            
            repo_name = repo['name']
            repo_link = f"[{repo_display}](https://git.smartcrec.com/{repo_name})"
            report.append(f"| {idx:2d} | {repo_link:70s} | {repo['total_lines']:10,} | {repo['additions']:7,} | {repo['deletions']:7,} | {repo['commits']:4d} | {repo['contributors_count']:3d} | {contributors_str} |")
        
        report.append("")
        report.append("-" * 80)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n报告已保存到: {output_file}")
        
        return report_text
    
    def export_json(self, stats, output_file):
        """导出 JSON 格式数据"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"JSON 数据已保存到: {output_file}")
