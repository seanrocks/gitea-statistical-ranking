#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gitea API 模块
负责与 Gitea API 交互，获取用户和仓库信息
"""

import requests
import base64


class GiteaAPI:
    """Gitea API 交互类"""
    
    def __init__(self, base_url, token=None, username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.username = username
        self.password = password
        self.headers = {}
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        elif self.username and self.password:
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            self.headers['Authorization'] = f'Basic {credentials}'
    
    def get_users(self):
        """获取所有用户列表，返回 {login: email} 的字典"""
        users = {}
        page = 1
        limit = 50
        
        while True:
            params = {
                'page': page,
                'limit': limit
            }
            response = requests.get(
                f'{self.base_url}/api/v1/admin/users',
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                
                for user in data:
                    if user.get('login'):
                        login = user['login']
                        is_active = user.get('active', True)
                        if is_active:
                            users[login] = {
                                'email': user.get('email', '').lower(),
                                'full_name': user.get('full_name', '')
                            }
                
                if len(data) < limit:
                    break
                
                page += 1
            else:
                return None
        
        return users
    
    def collect_users_from_repos(self):
        """从仓库中收集所有用户"""
        users = set()
        page = 1
        limit = 50
        
        while True:
            params = {
                'page': page,
                'limit': limit
            }
            response = requests.get(
                f'{self.base_url}/api/v1/repos/search',
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get('data'):
                break
            
            for repo in data['data']:
                owner = repo.get('owner', {})
                if owner.get('login'):
                    users.add(owner['login'])
            
            if len(data['data']) < limit:
                break
            
            page += 1
        
        return users
    
    def get_repos(self):
        """获取所有仓库列表，排除 fork 的仓库和 fork/ 开头的仓库"""
        # 直接使用组织接口获取仓库，避免 search 接口的限制和排序问题
        print(f"  使用组织接口获取仓库列表")
        return self._get_repos_by_orgs()
    
    def _get_repos_by_search(self):
        """使用 search 接口获取仓库列表（备用方法）"""
        repos = []
        page = 1
        limit = 50
        
        while True:
            params = {
                'q': '',  # 空搜索参数，获取所有仓库
                'page': page,
                'limit': limit
            }
            response = requests.get(
                f'{self.base_url}/api/v1/repos/search',
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data.get('data'):
                break
            
            for repo in data['data']:
                full_name = repo.get('full_name', '')
                repos.append(repo)
            
            if len(data['data']) == 0:
                break
            
            page += 1
        
        return repos
    
    def _get_repos_by_users(self):
        """遍历所有用户，获取每个用户的仓库列表（最后手段）"""
        repos = []
        users = self.get_users()
        
        for username, user_data in users.items():
            page = 1
            limit = 50
            
            while True:
                params = {
                    'page': page,
                    'limit': limit
                }
                response = requests.get(
                    f'{self.base_url}/api/v1/users/{username}/repos',
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                for repo in data:
                    full_name = repo.get('full_name', '')
                    repos.append(repo)
                
                if len(data) == 0:
                    break
                
                page += 1
        
        return repos
    
    def _get_repos_by_orgs(self):
        """遍历所有组织，获取每个组织的仓库列表"""
        repos = []
        
        # 获取所有组织
        orgs = self._get_orgs()
        
        for org_name in orgs:
            page = 1
            limit = 50
            
            while True:
                params = {
                    'page': page,
                    'limit': limit
                }
                response = requests.get(
                    f'{self.base_url}/api/v1/orgs/{org_name}/repos',
                    headers=self.headers,
                    params=params
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                for repo in data:
                    full_name = repo.get('full_name', '')
                    repos.append(repo)
                
                if len(data) == 0:
                    break
                
                page += 1
        
        return repos
    
    def _get_orgs(self):
        """获取所有组织"""
        orgs = []
        page = 1
        limit = 50
        
        while True:
            params = {
                'page': page,
                'limit': limit
            }
            response = requests.get(
                f'{self.base_url}/api/v1/admin/orgs',
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            if not data:
                break
            
            for org in data:
                org_name = org.get('username', '')
                if org_name:
                    orgs.append(org_name)
            
            if len(data) == 0:
                break
            
            page += 1
        
        return orgs
    
    def get_repo_commits(self, owner, repo_name, since=None):
        """获取指定仓库的所有提交记录（使用 API）"""
        commits = []
        page = 1
        limit = 50
        
        while True:
            params = {
                'page': page,
                'limit': limit
            }
            if since:
                params['since'] = since
            
            response = requests.get(
                f'{self.base_url}/api/v1/repos/{owner}/{repo_name}/commits',
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data:
                break
            
            commits.extend(data)
            
            if len(data) < limit:
                break
            
            page += 1
        
        return commits
