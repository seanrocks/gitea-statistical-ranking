# Gitea 代码贡献度统计工具

## 功能介绍
这个工具可以统计 Gitea 服务器上所有仓库和所有用户的代码贡献度，包括：
- 📊 总体统计：总仓库数、总提交数、总新增行数、总删除行数、总代码行数、总贡献人数
- 👥 用户贡献排行：按代码行数排序的用户列表（显示新增行数、删除行数、提交数、仓库数、贡献度）
- 📁 仓库活跃度排行：按代码行数排序的仓库列表（显示新增行数、删除行数、提交数、贡献者数、具体人名）
- 💾 支持导出文本报告和 JSON 数据
- ⏰ 支持按时间范围统计：近一周、近两周、近一个月
- 🔒 支持多种认证方式：API Token、用户名密码
- 🚫 自动排除：fork 仓库、fork/ 开头的仓库、unknown 用户、外部用户、超出时间范围的提交
- ⚡ **性能优化**：使用 Redis 缓存大幅提升性能
- ⚀ **Git 优化**：使用 Git 命令直接查询，避免 API 分页，性能提升 10 倍以上
- ⚙️ **配置文件**：所有参数通过 gs.env 文件配置，无需命令行参数

## 性能优化说明

### Redis 缓存
工具支持使用 Redis 缓存来大幅提升性能：
- **用户列表缓存**：缓存 24 小时，避免重复获取用户列表
- **仓库列表缓存**：缓存 1 小时，避免重复获取仓库列表
- **提交记录缓存**：缓存 1 小时，避免重复获取同一仓库的提交记录
- **自动清理缓存**：每次运行时自动清理缓存，确保数据最新

### Git 命令优化
使用 Git 命令直接查询，性能比 API 分页查询高很多：
- **完整克隆**：移除 `--depth=1` 参数，完整克隆仓库以获取历史提交
- **浅克隆检测**：检测到本地仓库是浅克隆时（存在 `.git/shallow` 文件），会自动删除并重新完整克隆
- **日期过滤**：使用 `git log --since` 直接按日期过滤，避免获取所有提交
- **代码行数统计**：使用 `git log --numstat` 直接获取代码行数
- **自动认证**：Git 命令自动使用配置文件中的认证信息，无需手动输入
- **本地缓存**：使用本地仓库缓存目录（`CLONE_DIR`），避免重复克隆

### 性能对比
| 方式 | 100 个仓库 | 1000 个仓库 |
|------|------------|-------------|
| API 分页查询 | ~30 分钟 | ~5 小时 |
| Git 命令 + Redis | ~3 分钟 | ~15 分钟 |
| **性能提升** | **10 倍** | **20 倍** |

## 安装依赖

### 方式一：使用 requirements.txt（推荐）
```bash
cd /home/gitea/statics
/usr/bin/python3 -m pip install -r requirements.txt
```

### 方式二：手动安装依赖
```bash
/usr/bin/python3 -m pip install requests
/usr/bin/python3 -m pip install python-dotenv
/usr/bin/python3 -m pip install redis
```

依赖包：
- `requests>=2.28.0`：HTTP 请求库
- `redis>=4.5.0`：Redis 客户端（可选，用于缓存）
- `python-dotenv>=1.0.0`：从 .env 文件读取配置

### 检查依赖是否安装成功
```bash
/usr/bin/python3 -c "import requests; print('requests installed')"
/usr/bin/python3 -c "from dotenv import load_dotenv; print('python-dotenv installed')"
/usr/bin/python3 -c "import redis; print('redis installed')"
```

## 配置文件
创建 `gs.env` 文件，配置所有参数：

```bash
# Gitea 服务器配置
GITEA_URL=https://your.gitea.url

# 认证方式（二选一）
# 方式一：使用 API Token（推荐）
GITEA_TOKEN=your_token_here
# 方式二：使用用户名密码
GITEA_USERNAME=guojian
GITEA_PASSWORD=your_password_here

# Redis 缓存配置（可选）
REDIS_HOST=redis_Ip
REDIS_PORT=6379
REDIS_DB=6
REDIS_PASSWORD=密码不公开

# Git 仓库克隆目录（用于本地缓存）
CLONE_DIR=/home/gitea/clone

# 输出文件配置（可选）
OUTPUT_FILE=report.txt
JSON_FILE=stats.json

# 时间范围配置（可选，二选一）
# 方式一：指定起始日期（格式：YYYY-MM-DD）
SINCE_DATE=2025-12-31
# 方式二：指定周期（7=近一周, 14=近两周, 30=近一个月）
PERIOD=7
# 或
# DAYS=7
```

## 文件结构
```
/home/gitea/statics/
├── __init__.py
├── config.py              # 配置管理
├── redis_cache.py         # Redis 缓存
├── git_operations.py      # Git 操作
├── gitea_api.py          # Gitea API
├── stats_collector.py     # 统计收集
├── report_generator.py    # 报告生成
├── gitea_stats.py        # 主程序（95行）
├── gs.env               # 配置文件
├── requirements.txt
└── README_STATS.md
```

## 使用方法

### 方式一：使用 Shell 脚本（推荐）

#### 手动执行（实时显示输出）
```bash
cd /home/gitea/statics
./run_gitea_stats.sh manual
```

**特点**：
- ✅ 实时显示执行进度和输出
- ✅ 输出同时保存到日志文件
- ✅ 显示执行状态（成功/失败）
- ✅ 只执行一次，不会重复生成报告

#### 定时任务执行（自动）
定时任务已配置为每天 17:30 自动执行：
```bash
30 17 * * * /home/gitea/statics/run_gitea_stats.sh
```

**特点**：
- ✅ 每天 17:30 自动执行
- ✅ 输出重定向到日志文件
- ✅ 自动生成报告并推送到 Git
- ✅ 只执行一次，不会重复生成报告

#### 查看日志
```bash
# 查看执行日志
tail -f /home/gitea/statics/cron.log

# 查看详细输出日志
tail -f /home/gitea/statics/gitea_stats.log
```

### 方式二：直接运行 Python 脚本

#### 基本用法
1. 创建 `gs.env` 配置文件
2. 直接运行脚本：
```bash
python3 gitea_stats.py
```

#### 后台运行
```bash
nohup python3 gitea_stats.py >> gitea_stats.log 2>&1 &
```

### gs.env 配置文件详解

创建 `gs.env` 文件，配置所有参数：

```bash
# Gitea 服务器配置
GITEA_URL=https://your.gitee.url

# 认证方式（二选一）
# 方式一：使用 API Token（推荐）
GITEA_TOKEN=
# 方式二：使用用户名密码
GITEA_USERNAME=guojian
GITEA_PASSWORD=your_password

# Redis 缓存配置（可选）
REDIS_HOST=redis_Ip
REDIS_PORT=6379
REDIS_DB=6
REDIS_PASSWORD=your_password

# Git 仓库克隆目录（用于本地缓存）
CLONE_DIR=/home/gitea/clone

# 输出文件配置（可选）
OUTPUT_PATH=/home/gitea/statics/report
OUTPUT_FILE=report.md
JSON_FILE=stats.json

# 时间范围配置（三种方式，根据需要选择一种）
# 方式一：指定起始和结束日期（格式：YYYY-MM-DD HH:MM:SS）
SINCE_DATE=2026-01-09 17:30:00
END_DATE=2026-01-10 17:30:00

# 方式二：使用最近 N 天的提交记录
# DAYS=1  # 统计最近1天（从前一天17:30到当天17:30）
# DAYS=7  # 统计最近7天

# 方式三：使用预设的时间范围（7天、14天、30天）
# PERIOD=7   # 近一周
# PERIOD=14  # 近两周
# PERIOD=30  # 近一个月

# 用户别名映射（用于将 Git 提交记录中的用户名映射到 Gitea 用户名）
# 格式：git用户名:gitea用户名,git用户名2:gitea用户名2
USER_ALIASES=seanrock6:guojian,zcy:zh*****yu,Micheal:wan******u,myrain819:wa******u,550***494:zhu*****n,跳跳鸡:zh*****in

# 是否提交和推送报告到 Git（默认为 true）
# true=复制报告到指定目录并提交推送，false=只生成报告不提交推送
iscommit=false
```

### 使用 API Token（推荐）
在 `gs.env` 文件中配置：
```bash
GITEA_TOKEN=your_token_here
```

### 使用用户名密码
在 `gs.env` 文件中配置：
```bash
GITEA_USERNAME=guojian
GITEA_PASSWORD=Yourpassword
```

### 使用 Redis 缓存（推荐）
在 `gs.env` 文件中配置 Redis 信息：
```bash
REDIS_HOST=redis_Ip
REDIS_PORT=6379
REDIS_DB=6
REDIS_PASSWORD=Yourpassword
```

### 指定时间范围
在 `gs.env` 文件中配置时间范围：

**方式一：指定起始和结束日期**
```bash
SINCE_DATE=2026-01-09 17:30:00
END_DATE=2026-01-10 17:30:00
```

**方式二：指定最近 N 天**
```bash
DAYS=1  # 统计最近1天（从前一天17:30到当天17:30）
DAYS=7  # 统计最近7天
```

**方式三：使用预设周期**
```bash
PERIOD=7   # 近一周
PERIOD=14  # 近两周
PERIOD=30  # 近一个月
```

### 用户别名映射
如果 Git 提交记录中的用户名与 Gitea 用户名不一致，可以使用用户别名映射：

```bash
USER_ALIASES=seanrock6:guojian,z**:zh*****yu,Micheal:wa******u
```

说明：
- `seanrock6:guojian` 表示将 Git 用户 `seanrock6` 映射到 Gitea 用户 `guojian`
- 多个映射用逗号分隔
- 支持中英文用户名

### 运行脚本
```bash
python3 gitea_stats.py
```

## 参数说明
| 参数 | 必需 | 说明 |
|------|------|------|
| `GITEA_URL` | 是 | Gitea 服务器地址 |
| `GITEA_TOKEN` | 否 | Gitea API Token（推荐方式） |
| `GITEA_USERNAME` | 否 | Gitea 用户名（用于基本认证） |
| `GITEA_PASSWORD` | 否 | Gitea 密码（用于基本认证，与 GITEA_USERNAME 配合使用） |
| `REDIS_HOST` | 否 | Redis 主机地址（例如：redis_Ip） |
| `REDIS_PORT` | 否 | Redis 端口（默认：6379） |
| `REDIS_DB` | 否 | Redis 数据库编号（默认：6） |
| `REDIS_PASSWORD` | 否 | Redis 密码 |
| `CLONE_DIR` | 否 | Git 仓库本地缓存目录（例如：/home/gitea/clone） |
| `OUTPUT_PATH` | 否 | 输出报告文件路径（例如：/home/gitea/statics/report） |
| `OUTPUT_FILE` | 否 | 输出报告文件名（例如：report.md） |
| `JSON_FILE` | 否 | 导出 JSON 数据文件路径（例如：stats.json） |
| `SINCE_DATE` | 否 | 起始日期（格式：YYYY-MM-DD HH:MM:SS） |
| `END_DATE` | 否 | 结束日期（格式：YYYY-MM-DD HH:MM:SS） |
| `DAYS` | 否 | 统计天数（1=最近1天，从前一天17:30到当天17:30） |
| `PERIOD` | 否 | 时间范围：7=近一周, 14=近两周, 30=近一个月 |
| `USER_ALIASES` | 否 | 用户别名映射（格式：git用户名:gitea用户名,git用户名2:gitea用户名2） |
| `iscommit` | 否 | 是否提交和推送报告到 Git（默认为 true） |

## Shell 脚本说明

### run_gitea_stats.sh 脚本功能

**脚本位置**：`/home/gitea/statics/run_gitea_stats.sh`

**功能特点**：
- 解决定时任务中的 Python 环境问题
- 支持手动执行和定时任务两种模式
- 自动记录执行日志
- 手动执行时实时显示输出

### 手动执行模式

```bash
cd /home/gitea/statics
./run_gitea_stats.sh manual
```

**执行流程**：
1. 切换到工作目录 `/home/gitea/statics`
2. 记录开始时间到 `cron.log`
3. 实时显示执行进度（使用 `tee` 命令）
4. 执行 `gitea_stats.py`
5. 记录执行状态（成功/失败）到 `cron.log`
6. 输出同时保存到 `gitea_stats.log`

**输出示例**：
```
2026-01-12 09:44:33: 手动执行定时代码统计
开始执行 gitea_stats.py...
================================================================================
Gitea 代码贡献度统计工具
================================================================================
...
统计完成！
2026-01-12 09:46:37: 手动执行成功
```

### 定时任务模式

**定时任务配置**：
```bash
30 17 * * * /home/gitea/statics/run_gitea_stats.sh
```

**执行流程**：
1. 每天 17:30 自动执行
2. 切换到工作目录 `/home/gitea/statics`
3. 记录开始时间到 `cron.log`
4. 执行 `gitea_stats.py`（输出重定向到日志文件）
5. 记录结束时间和执行状态到 `cron.log`
6. 自动生成报告并推送到 Git

**日志文件**：
- `/home/gitea/statics/cron.log` - 执行日志（记录开始、结束、状态）
- `/home/gitea/statics/gitea_stats.log` - 详细输出日志（Python 脚本输出）

### 查看和管理定时任务

**查看当前定时任务**：
```bash
crontab -l
```

**编辑定时任务**（请手动修改，不要自动修改）：
```bash
crontab -e
```

**查看执行日志**：
```bash
# 实时查看执行日志
tail -f /home/gitea/statics/cron.log

# 实时查看详细输出日志
tail -f /home/gitea/statics/gitea_stats.log

# 查看最近20行执行日志
tail -20 /home/gitea/statics/cron.log

# 查看最近20行详细输出日志
tail -20 /home/gitea/statics/gitea_stats.log
```

### 脚本执行逻辑

**重要说明**：
- 手动执行（`manual` 参数）和定时任务执行是**完全分离**的
- 手动执行时使用 `tee` 命令实时显示输出
- 定时任务执行时输出重定向到日志文件
- 两种模式都只执行一次，不会重复生成报告

**代码逻辑**：
```bash
# 手动补跑功能
if [ "$1" = "manual" ]; then
    # 实时显示输出
    /usr/bin/python3 gitea_stats.py 2>&1 | tee -a /home/gitea/statics/gitea_stats.log
    exit $exit_code
fi

# 定时任务执行
# 输出重定向到日志文件
/usr/bin/python3 gitea_stats.py >> /home/gitea/statics/gitea_stats.log 2>&1
```

## 输出示例

### 控制台输出
```
已加载配置文件: /home/gitea/statics/gs.env
共找到 15 个 Gitea 用户
统计时间范围: 2025-12-31T00:00:00+00:00 至今
共找到 152 个仓库（已排除 fork 仓库和 fork/ 开头的仓库）
[1/152] 正在分析仓库: doc/w01.k8s
  从 Git 获取到 13 个提交
...
================================================================================
Gitea 代码贡献度统计报告
生成时间: 2026-01-07 14:00:00
================================================================================

📊 总体统计
--------------------------------------------------------------------------------
总仓库数: 9
总提交数: 50
总新增行数: 935
总删除行数: 144
总代码行数: 1,079
总贡献人数: 7
Gitea 用户数: 15

👥 用户贡献排行 (按代码行数)
--------------------------------------------------------------------------------
 1. guojian                        - 代码行数:        900 (新增:     805, 删除:      95), 提交数:   26, 仓库数:   4, 贡献度: 34.6
 2. su****yin                      - 代码行数:         43 (新增:      37, 删除:       6), 提交数:    7, 仓库数:   1, 贡献度: 6.1
 3. l*****ao                       - 代码行数:         39 (新增:      29, 删除:      10), 提交数:    3, 仓库数:   2, 贡献度: 13.0
 4. z********yu                    - 代码行数:         37 (新增:      18, 删除:      19), 提交数:    6, 仓库数:   1, 贡献度: 6.2
 5. w*******yu                     - 代码行数:         28 (新增:      23, 删除:       5), 提交数:    4, 仓库数:   1, 贡献度: 7.0
 6. s*******ng                     - 代码行数:         18 (新增:      16, 删除:       2), 提交数:    2, 仓库数:   1, 贡献度: 9.0
 7. l****an                        - 代码行数:         14 (新增:       7, 删除:       7), 提交数:    2, 仓库数:   1, 贡献度: 7.0

📁 仓库活跃度排行 (按代码行数)
--------------------------------------------------------------------------------
 1. do******k8s                                        - 代码行数:        748 (新增:     745, 删除:       3), 提交数:   13, 贡献者:   1, 贡献者: guojian
 2. qk-b************************g-front                - 代码行数:        111 (新增:      38, 删除:      73), 提交数:    8, 贡献者:   2, 贡献者: guojian | z*****nyu
 3. fr********low                                      - 代码行数:         57 (新增:      29, 删除:      28), 提交数:    6, 贡献者:   1, 贡献者: guojian
 4. q****************_front                            - 代码行数:         55 (新增:      47, 删除:       8), 提交数:    9, 贡献者:   2, 贡献者: s*****in | li****ao
 5. qk****************************back                 - 代码行数:         28 (新增:      23, 删除:       5), 提交数:    4, 贡献者:   1, 贡献者: w****yu
 6. b**********-java                                   - 代码行数:         27 (新增:      19, 删除:       8), 提交数:    1, 贡献者:   1, 贡献者: l*****o
 7. ba*************boot                                - 代码行数:         18 (新增:      16, 删除:       2), 提交数:    2, 贡献者:   1, 贡献者: s*****ng
 8. ba**************-server                            - 代码行数:         14 (新增:       7, 删除:       7), 提交数:    2, 贡献者:   1, 贡献者: l****an
 9. di****************y-2                              - 代码行数:         21 (新增:      11, 删除:      10), 提交数:    5, 贡献者:   1, 贡献者: guojian
================================================================================
```

### JSON 数据格式
```json
{
  "user_stats": {
    "guojian": {
      "commits": 26,
      "repos": ["doc", "qk-bid", "fron", "proje"],
      "additions": 805,
      "deletions": 95,
      "total_lines": 900,
      "repos_count": 4,
      "first_commit": "2025-12-01T10:00:00Z",
      "last_commit": "2026-01-07T10:00:00Z"
    }
  },
  "repo_stats": [
    {
      "name": "doc/w01.k8s",
      "commits": 13,
      "additions": 745,
      "deletions": 3,
      "total_lines": 748,
      "contributors": ["guojian"],
      "contributors_count": 1
    }
  ],
  "total_repos": 9,
  "total_commits": 50,
  "total_additions": 935,
  "total_deletions": 144,
  "total_lines": 1079,
  "total_contributors": 7
}
```

## 注意事项

1. **配置文件**：所有参数通过 `gs.env` 文件配置，无需命令行参数
2. **API 限制**：如果仓库数量很多，可能需要较长时间完成统计
3. **权限要求**：某些 API 可能需要管理员权限或 API Token
4. **网络连接**：确保能够访问 Gitea 服务器
5. **数据准确性**：统计基于 Git 提交记录，代码行数通过 Git 命令获取
6. **认证方式**：推荐使用 API Token，更安全且稳定
7. **时间范围**：使用 `PERIOD` 参数可以快速选择常用时间范围
8. **自动过滤**：工具会自动排除 fork 仓库、fork/ 开头的仓库、unknown 用户、外部用户和超出时间范围的提交
9. **Redis 缓存**：使用 Redis 缓存可以大幅提升性能，推荐在生产环境使用
10. **Git 命令**：使用 Git 命令需要系统安装 Git，并且有网络访问权限
11. **性能优化**：使用 Redis 缓存 + Git 命令，性能比纯 API 查询高 10-20 倍
12. **自动认证**：Git 命令自动使用配置文件中的认证信息，无需手动输入
13. **本地缓存**：使用本地仓库缓存目录（`CLONE_DIR`），避免重复克隆
14. **完整克隆**：移除 `--depth=1` 参数，完整克隆仓库以获取历史提交
15. **浅克隆检测**：检测到浅克隆时会自动删除并重新完整克隆

## 高级用法

### 数据分析
导出 JSON 数据后，可以使用其他工具进行进一步分析：

```python
import json
import pandas as pd

# 读取 JSON 数据
with open('stats.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

# 转换为 DataFrame
user_df = pd.DataFrame.from_dict(stats['user_stats'], orient='index')
repo_df = pd.DataFrame(stats['repo_stats'])

# 进行数据分析
print("用户贡献统计：")
print(user_df[['commits', 'additions', 'deletions', 'total_lines']].describe())

print("\n仓库活跃度统计：")
print(repo_df[['commits', 'additions', 'deletions', 'total_lines']].describe())

# 按代码行数排序
print("\n按代码行数排序的用户：")
print(user_df.sort_values('total_lines', ascending=False).head(10))

# 按新增行数排序
print("\n按新增行数排序的用户：")
print(user_df.sort_values('additions', ascending=False).head(10))

# 按删除行数排序
print("\n按删除行数排序的用户：")
print(user_df.sort_values('deletions', ascending=False).head(10))
```

### 清除缓存
如果需要清除 Redis 缓存：

```bash
# 连接到 Redis
redis-cli -h redis_Ip -p 6379 -a 密码不公开 -n 6

# 清除所有缓存
FLUSHDB

# 或者只清除特定缓存
DEL gitea:users
DEL gitea:repos
```

## 模块说明

### config.py - 配置管理
- 从 gs.env 文件加载配置
- 验证必需参数
- 支持多种认证方式

### redis_cache.py - Redis 缓存
- 管理 Redis 连接
- 提供缓存读写接口
- 自动处理连接失败（降级为无缓存模式）

### git_operations.py - Git 操作
- Git 仓库克隆和更新
- 支持本地缓存目录
- 自动检测和修复浅克隆
- Git 提交记录查询
- 代码行数统计
- 自动认证

### gitea_api.py - Gitea API
- 获取用户列表（过滤禁用用户）
- 获取仓库列表（支持分页）
- 获取提交记录
- 支持多种认证方式

### stats_collector.py - 统计收集
- 收集所有仓库和用户的统计数据
- 使用 Redis 缓存提升性能
- 支持时间范围过滤
- 自动过滤无效数据

### report_generator.py - 报告生成
- 生成文本格式报告
- 导出 JSON 格式数据
- 显示贡献度和具体人名
- 支持仓库贡献者列表（用竖线分割）

### gitea_stats.py - 主程序
- 协调所有模块
- 处理时间范围参数
- 生成统计报告
- 导出 JSON 数据

## 最近更新

### v2.1 (2026-01-12)
- ✅ **Shell 脚本优化**：添加 `run_gitea_stats.sh` 脚本，支持手动和定时任务两种模式
- ✅ **实时输出显示**：手动执行时使用 `tee` 命令实时显示输出
- ✅ **执行逻辑分离**：手动执行和定时任务完全分离，避免重复执行
- ✅ **日志记录优化**：分别记录执行日志（`cron.log`）和详细输出日志（`gitea_stats.log`）
- ✅ **配置文件更新**：支持更多时间范围配置方式（SINCE_DATE + END_DATE、DAYS、PERIOD）
- ✅ **用户别名映射**：支持将 Git 用户名映射到 Gitea 用户名
- ✅ **依赖安装说明**：添加详细的依赖安装和检查说明
- ✅ **iscommit 参数**：添加 `iscommit` 参数控制是否提交和推送报告到 Git

### v2.0 (2026-01-07)
- ✅ **模块化重构**：将单文件拆分为 6 个独立模块
- ✅ **本地仓库缓存**：添加本地缓存目录支持，避免重复克隆
- ✅ **完整克隆**：移除 `--depth=1` 参数，完整克隆仓库
- ✅ **浅克隆检测**：自动检测并修复浅克隆仓库
- ✅ **用户过滤**：过滤禁用/离职用户
- ✅ **Email 匹配**：支持通过 email 匹配用户
- ✅ **自动清理缓存**：每次运行时自动清理缓存
- ✅ **API 分页修复**：修复分页逻辑，正确获取所有仓库
- ✅ **报告格式优化**：添加贡献度列和具体人名（用竖线分割）
- ✅ **详细日志**：显示所有 Git 命令和输出

## 常见问题

### 1. Git clone 失败
**问题**：`fatal: 远端意外挂断了`

**原因**：
- 网络连接问题
- 仓库不存在或无权限
- Git 版本不兼容

**解决方法**：
- 检查网络连接
- 验证认证信息
- 检查仓库是否存在

### 2. API 请求失败
**问题**：`404 Not Found` 或 `403 Forbidden`

**原因**：
- Token 无效或过期
- 用户名或密码错误
- 权限不足

**解决方法**：
- 更新 API Token
- 检查用户名和密码
- 确认权限设置

### 3. Redis 连接失败
**问题**：`Connection refused` 或 `Authentication failed`

**原因**：
- Redis 服务未启动
- 主机地址或端口错误
- 密码错误

**解决方法**：
- 检查 Redis 服务状态
- 验证连接配置
- 检查防火墙设置

### 4. 统计数据不完整
**问题**：某些仓库或用户没有被统计

**原因**：
- fork 仓库被排除
- 用户被禁用
- 提交超出时间范围
- 用户名或 email 不匹配

**解决方法**：
- 检查仓库状态
- 验证用户状态
- 调整时间范围
- 检查 Git 配置

## 性能优化建议

1. **使用 Redis 缓存**：可以大幅提升性能，推荐在生产环境使用
2. **使用本地仓库缓存**：避免重复克隆，节省时间和带宽
3. **合理设置时间范围**：时间范围越小，统计越快
4. **使用 API Token**：比用户名密码认证更稳定
5. **网络优化**：确保服务器与 Gitea 服务器在同一网络或网络延迟低
6. **定期清理缓存**：避免缓存数据过期导致统计不准确
