#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计收集模块
负责收集和统计所有仓库和用户的代码贡献数据
"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from redis_cache import RedisCache
from gitea_api import GiteaAPI
from git_operations import GitOperations


class StatsCollector:
    """统计数据收集类"""
    
    def __init__(self, config):
        self.base_url = config.get('GITEA_URL')
        self.token = config.get('GITEA_TOKEN')
        self.username = config.get('GITEA_USERNAME')
        self.password = config.get('GITEA_PASSWORD')
        self.clone_dir = config.get('CLONE_DIR')
        
        self.gitea_api = GiteaAPI(self.base_url, self.token, self.username, self.password)
        self.git_ops = GitOperations(self.token, self.username, self.password, self.clone_dir)
        
        self.redis_cache = None
        if config.get('REDIS_HOST'):
            self.redis_cache = RedisCache(
                host=config.get('REDIS_HOST'),
                port=int(config.get('REDIS_PORT', 6379)),
                db=int(config.get('REDIS_DB', 6)),
                password=config.get('REDIS_PASSWORD')
            )
        
        self.gitea_users = {}
        
        self.user_aliases = {}
        if config.get('USER_ALIASES'):
            aliases_str = config.get('USER_ALIASES')
            for alias_pair in aliases_str.split(','):
                parts = alias_pair.split(':')
                if len(parts) == 2:
                    self.user_aliases[parts[0].strip()] = parts[1].strip()
    
    def cache_get(self, key, default=None):
        """从 Redis 缓存获取数据"""
        if not self.redis_cache or not self.redis_cache.enabled:
            return default
        return self.redis_cache.get(key, default)
    
    def cache_set(self, key, value, expire_seconds=3600):
        """设置 Redis 缓存"""
        if not self.redis_cache or not self.redis_cache.enabled:
            return
        self.redis_cache.set(key, value, expire_seconds)
    
    def get_gitea_users(self):
        """获取 Gitea 中所有用户列表"""
        cache_key = "gitea:users"
        
        users = self.gitea_api.get_users()
        
        if users:
            print(f"共找到 {len(users)} 个 Gitea 用户")
            self.cache_set(cache_key, users, expire_seconds=86400)
        
        return users if users else {}
    
    def get_all_repos(self):
        """获取所有仓库列表，排除 fork 的仓库和 fork/ 开头的仓库"""
        cache_key = "gitea:repos"
        
        repos = self.gitea_api.get_repos()
        
        if repos:
            print(f"共找到 {len(repos)} 个仓库（已排除 fork 仓库和 fork/ 开头的仓库）")
            self.cache_set(cache_key, repos, expire_seconds=3600)
        
        return repos if repos else []
    
    def parse_datetime(self, dt_str):
        """解析 datetime 字符串，返回带时区的 datetime 对象"""
        if not dt_str:
            return None
        
        if isinstance(dt_str, str):
            dt_str = dt_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            return dt
        
        if dt_str.tzinfo is None:
            return dt_str.replace(tzinfo=timezone.utc)
        
        return dt_str
    
    def get_repo_commits(self, repo_url, since_date=None, until_date=None):
        """获取仓库的提交记录（优先使用 Git 命令）"""
        cache_key = f"gitea:commits:{repo_url}:{since_date}:{until_date}"
        cached_commits = self.cache_get(cache_key)
        if cached_commits:
            print(f"  从缓存读取提交记录: {len(cached_commits)} 个提交")
            return cached_commits
        
        commits = self.git_ops.get_repo_commits(repo_url, since_date, until_date)
        
        if commits:
            print(f"  从 Git 获取到 {len(commits)} 个提交")
            self.cache_set(cache_key, commits, expire_seconds=3600)
        
        return commits
    
    def collect_all_stats(self, since_date=None, until_date=None):
        """收集所有仓库和用户的统计数据"""
        print("开始收集统计数据...")
        
        self.gitea_users = self.get_gitea_users()
        
        time_range_str = ""
        if since_date and until_date:
            time_range_str = f"{since_date} 至 {until_date}"
        elif since_date:
            time_range_str = f"{since_date} 至今"
        elif until_date:
            time_range_str = f"至 {until_date}"
        
        print(f"统计时间范围: {time_range_str}" if time_range_str else "统计所有时间")
        
        repos = self.get_all_repos()
        
        user_stats = defaultdict(lambda: {
            'commits': 0,
            'repos': set(),
            'additions': 0,
            'deletions': 0,
            'total_lines': 0,
            'first_commit': None,
            'last_commit': None
        })
        
        repo_stats = []
        skipped_unknown_count = 0
        skipped_outside_count = 0
        skipped_repos_count = 0
        
        for idx, repo in enumerate(repos, 1):
            owner = repo.get('owner', {}).get('login', 'unknown')
            repo_name = repo.get('name', 'unknown')
            full_name = f"{owner}/{repo_name}"
            clone_url = repo.get('clone_url', f"{self.base_url}/{owner}/{repo_name}.git")
            
            print(f"[{idx}/{len(repos)}] 正在分析仓库: {full_name}")
            
            commits = self.get_repo_commits(clone_url, since_date, until_date)
            
            if not commits:
                print(f"  跳过仓库: {full_name} (在指定时间内无提交)")
                skipped_repos_count += 1
                continue
            
            repo_stat = {
                'name': full_name,
                'description': repo.get('description', ''),
                'commits': 0,
                'additions': 0,
                'deletions': 0,
                'total_lines': 0,
                'contributors': set()
            }
            
            for commit in commits:
                author = commit.get('author', {})
                username = author.get('login') or author.get('name') or 'unknown'
                
                if username == 'unknown':
                    skipped_unknown_count += 1
                    continue
                
                author_email = author.get('email', '').lower()
                matched_user = None
                
                if username in self.user_aliases:
                    username = self.user_aliases[username]
                
                if username in self.gitea_users:
                    matched_user = username
                elif author_email in [user_data.get('email', '').lower() for user_data in self.gitea_users.values()]:
                    for login, user_data in self.gitea_users.items():
                        if user_data.get('email', '').lower() == author_email:
                            matched_user = login
                            break
                else:
                    for login, user_data in self.gitea_users.items():
                        login_lower = login.lower()
                        username_lower = username.lower().replace(' ', '')
                        if login_lower == username_lower or login_lower in username_lower or username_lower in login_lower:
                            matched_user = login
                            break
                
                if not matched_user:
                    skipped_outside_count += 1
                    continue
                
                stats = commit.get('stats', {})
                additions = stats.get('additions', 0) or 0
                deletions = stats.get('deletions', 0) or 0
                total = stats.get('total', 0) or additions + deletions
                
                commit_info = commit.get('commit', {})
                committer_info = commit_info.get('committer', {})
                commit_date_str = committer_info.get('date')
                
                if commit_date_str:
                    commit_dt = self.parse_datetime(commit_date_str)
                    
                    if commit_dt:
                        commit_date_iso = commit_dt.isoformat()
                        
                        user_stats[matched_user]['commits'] += 1
                        user_stats[matched_user]['repos'].add(full_name)
                        user_stats[matched_user]['additions'] += additions
                        user_stats[matched_user]['deletions'] += deletions
                        user_stats[matched_user]['total_lines'] += total
                        repo_stat['contributors'].add(matched_user)
                        repo_stat['commits'] += 1
                        repo_stat['additions'] += additions
                        repo_stat['deletions'] += deletions
                        repo_stat['total_lines'] += total
                        
                        if user_stats[matched_user]['first_commit'] is None:
                            user_stats[matched_user]['first_commit'] = commit_date_iso
                        else:
                            first_dt = self.parse_datetime(user_stats[matched_user]['first_commit'])
                            if first_dt and commit_dt < first_dt:
                                user_stats[matched_user]['first_commit'] = commit_date_iso
                        
                        if user_stats[matched_user]['last_commit'] is None:
                            user_stats[matched_user]['last_commit'] = commit_date_iso
                        else:
                            last_dt = self.parse_datetime(user_stats[matched_user]['last_commit'])
                            if last_dt and commit_dt > last_dt:
                                user_stats[matched_user]['last_commit'] = commit_date_iso
            
            if repo_stat['commits'] > 0:
                repo_stat['contributors'] = list(repo_stat['contributors'])
                repo_stat['contributors_count'] = len(repo_stat['contributors'])
                repo_stats.append(repo_stat)
                if full_name == 'pca/pc_attendance_back':
                    print(f"  调试: 添加仓库到列表 - {full_name}, 提交数: {repo_stat['commits']}, 代码行数: {repo_stat['total_lines']}")
            else:
                if full_name == 'pca/pc_attendance_back':
                    print(f"  调试: 跳过仓库 - {full_name}, 提交数: {repo_stat['commits']}")
        
        print(f"\n跳过统计:")
        print(f"  - 仓库（无提交）: {skipped_repos_count} 个仓库")
        print(f"  - unknown 用户: {skipped_unknown_count} 个提交")
        print(f"  - 外部用户（非 Gitea 账户）: {skipped_outside_count} 个提交")
        
        for username in user_stats:
            user_stats[username]['repos'] = list(user_stats[username]['repos'])
            user_stats[username]['repos_count'] = len(user_stats[username]['repos'])
        
        return {
            'user_stats': dict(user_stats),
            'repo_stats': repo_stats,
            'total_repos': len(repo_stats),
            'total_commits': sum(r['commits'] for r in repo_stats),
            'total_additions': sum(r['additions'] for r in repo_stats),
            'total_deletions': sum(r['deletions'] for r in repo_stats),
            'total_lines': sum(r['total_lines'] for r in repo_stats)
        }
