#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 操作模块
负责 Git 仓库的克隆、日志查询等操作
"""

import subprocess
import tempfile
import shutil
import shlex
import os
from urllib.parse import urlparse, quote


class GitOperations:
    """Git 操作类"""
    
    def __init__(self, token=None, username=None, password=None, clone_dir=None):
        self.token = token
        self.username = username
        self.password = password
        self.clone_dir = clone_dir
        
        if self.clone_dir and not os.path.exists(self.clone_dir):
            os.makedirs(self.clone_dir, exist_ok=True)
    
    def get_auth_url(self, url):
        """获取带认证信息的 URL"""
        if self.token:
            parsed = urlparse(url)
            auth_url = f"{parsed.scheme}://oauth2:{self.token}@{parsed.netloc}{parsed.path}"
            return auth_url
        elif self.username and self.password:
            parsed = urlparse(url)
            encoded_password = quote(self.password, safe='')
            auth_url = f"{parsed.scheme}://{self.username}:{encoded_password}@{parsed.netloc}{parsed.path}"
            return auth_url
        else:
            return url
    
    def clone_repo(self, repo_url, since_date=None, timeout=300):
        """克隆仓库到本地缓存目录或临时目录"""
        repo_name = self._extract_repo_name(repo_url)
        
        if self.clone_dir:
            local_path = os.path.join(self.clone_dir, repo_name)
            
            if os.path.exists(local_path):
                shallow_file = os.path.join(local_path, '.git', 'shallow')
                if os.path.exists(shallow_file):
                    print(f"  检测到浅克隆仓库，删除后重新完整克隆: {repo_name}")
                    shutil.rmtree(local_path)
                    print(f"  本地仓库不存在，执行 git clone: {repo_name}")
                    return self._clone_to_dir(repo_url, local_path, timeout)
                else:
                    print(f"  本地仓库已存在，执行 git fetch --all 更新: {repo_name}")
                    return self._pull_repo(local_path, repo_url, timeout)
            else:
                print(f"  本地仓库不存在，执行 git clone: {repo_name}")
                return self._clone_to_dir(repo_url, local_path, timeout)
        else:
            temp_dir = tempfile.mkdtemp()
            print(f"  克隆到临时目录: {temp_dir}")
            return self._clone_to_dir(repo_url, temp_dir, timeout)
    
    def _extract_repo_name(self, repo_url):
        """从 URL 中提取仓库名称"""
        parsed = urlparse(repo_url)
        path = parsed.path
        if path.endswith('.git'):
            path = path[:-4]
        if path.startswith('/'):
            path = path[1:]
        return path
    
    def _clone_to_dir(self, repo_url, target_dir, timeout=300):
        """克隆仓库到指定目录"""
        try:
            auth_url = self.get_auth_url(repo_url)
            clone_cmd = ['git', 'clone', auth_url, target_dir]
            
            print(f"  执行命令: {' '.join(clone_cmd)}")
            result = subprocess.run(clone_cmd, check=True, capture_output=True, text=True, timeout=timeout)
            
            if result.stdout:
                print(f"  输出: {result.stdout}")
            if result.stderr:
                print(f"  错误: {result.stderr}")
            
            return target_dir
        except subprocess.CalledProcessError as e:
            print(f"  Git 命令执行失败 (退出码 {e.returncode}):")
            if e.stdout:
                print(f"  标准输出: {e.stdout}")
            if e.stderr:
                print(f"  标准错误: {e.stderr}")
            if os.path.exists(target_dir) and target_dir.startswith('/tmp'):
                shutil.rmtree(target_dir)
            raise e
        except Exception as e:
            print(f"  Git 操作异常: {type(e).__name__}: {e}")
            if os.path.exists(target_dir) and target_dir.startswith('/tmp'):
                shutil.rmtree(target_dir)
            raise e
    
    def _pull_repo(self, local_path, repo_url, timeout=300):
        """更新本地仓库"""
        try:
            auth_url = self.get_auth_url(repo_url)
            
            fetch_cmd = ['git', '-C', local_path, 'fetch', '--all', '--prune']
            
            print(f"  执行命令: {' '.join(fetch_cmd)}")
            result = subprocess.run(fetch_cmd, check=True, capture_output=True, text=True, timeout=timeout)
            
            if result.stdout:
                print(f"  输出: {result.stdout}")
            if result.stderr:
                print(f"  错误: {result.stderr}")
            
            pull_cmd = ['git', '-C', local_path, 'pull']
            
            print(f"  执行命令: {' '.join(pull_cmd)}")
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=timeout)
            
            if pull_result.stdout:
                print(f"  输出: {pull_result.stdout}")
            if pull_result.stderr:
                print(f"  错误: {pull_result.stderr}")
            
            if pull_result.returncode != 0:
                print(f"  Git pull 执行失败 (退出码 {pull_result.returncode})，但 fetch 已成功，继续使用本地数据")
            
            return local_path
        except subprocess.CalledProcessError as e:
            print(f"  Git fetch 失败 (退出码 {e.returncode})，尝试重新克隆:")
            if e.stdout:
                print(f"  标准输出: {e.stdout}")
            if e.stderr:
                print(f"  标准错误: {e.stderr}")
            
            shutil.rmtree(local_path)
            return self._clone_to_dir(repo_url, local_path, timeout)
        except Exception as e:
            print(f"  Git 操作异常: {e}")
            raise e
    
    def get_commits_with_stats(self, repo_path, since_date=None, until_date=None, timeout=300):
        """获取仓库的提交记录和代码行数统计"""
        if since_date and until_date:
            log_cmd = ["git", "-C", repo_path, "log", "--all", "--since", since_date, "--until", until_date, "--pretty=format:AUTHOR:%an<%ae> %aI", "--numstat"]
        elif since_date:
            log_cmd = ["git", "-C", repo_path, "log", "--all", "--since", since_date, "--pretty=format:AUTHOR:%an<%ae> %aI", "--numstat"]
        elif until_date:
            log_cmd = ["git", "-C", repo_path, "log", "--all", "--until", until_date, "--pretty=format:AUTHOR:%an<%ae> %aI", "--numstat"]
        else:
            log_cmd = ["git", "-C", repo_path, "log", "--all", "--pretty=format:AUTHOR:%an<%ae> %aI", "--numstat"]
        
        result = subprocess.run(log_cmd, check=True, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            print(f"  Git log 命令执行失败: {result.stderr}")
            return []
        
        commits = []
        lines = result.stdout.strip().split('\n')
        print(f"  Git log 输出 {len(lines)} 行")
        
        current_commit = None
        
        for line in lines:
            if line.startswith('AUTHOR:'):
                if current_commit is not None:
                    commits.append(current_commit)
                
                parts = line[7:].split('<')
                if len(parts) >= 2:
                    author = parts[0]
                    author_email = parts[1].replace('>', '')
                    commit_date = parts[1].split('>')[-1].strip()
                    
                    current_commit = {
                        'sha': '',
                        'author': {
                            'login': author,
                            'name': author,
                            'email': author_email
                        },
                        'commit': {
                            'committer': {
                                'date': commit_date
                            }
                        },
                        'stats': {
                            'additions': 0,
                            'deletions': 0,
                            'total': 0
                        }
                    }
                continue
            
            if current_commit is None:
                continue
            
            if not line.strip():
                continue
            
            stats_parts = line.split('\t')
            if len(stats_parts) >= 2:
                add_raw = stats_parts[0].strip()
                del_raw = stats_parts[1].strip()
                
                if add_raw and add_raw.isdigit():
                    current_commit['stats']['additions'] += int(add_raw)
                if del_raw and del_raw.isdigit():
                    current_commit['stats']['deletions'] += int(del_raw)
                current_commit['stats']['total'] = current_commit['stats']['additions'] + current_commit['stats']['deletions']
        
        if current_commit is not None:
            commits.append(current_commit)
        
        print(f"  从 Git 获取到 {len(commits)} 个提交")
        
        return commits
    
    def get_repo_commits(self, repo_url, since_date=None, until_date=None, timeout=300):
        """获取仓库的提交记录（包含克隆和查询）"""
        repo_path = None
        is_temp = False
        
        try:
            repo_path = self.clone_repo(repo_url, since_date, timeout)
            is_temp = repo_path.startswith('/tmp')
            commits = self.get_commits_with_stats(repo_path, since_date, until_date, timeout)
            return commits
        except subprocess.TimeoutExpired:
            print(f"  Git 操作超时，跳过仓库: {repo_url}")
            return []
        except Exception as e:
            print(f"  Git 操作失败: {e}，跳过仓库: {repo_url}")
            return []
        finally:
            if is_temp and repo_path and os.path.exists(repo_path):
                shutil.rmtree(repo_path)
