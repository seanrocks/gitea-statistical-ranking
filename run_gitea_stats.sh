#!/bin/bash
# 每日 17:30 调用 gitea_stats.py 的脚本
# 解决定时任务中 Python 环境问题

# 设置环境变量
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="/root"
export USER="root"

# 设置工作目录
cd /home/gitea/statics

# 手动补跑功能
if [ "$1" = "manual" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): 手动执行定时代码统计" | tee -a /home/gitea/statics/cron.log
    echo "开始执行 gitea_stats.py..."
    /usr/bin/python3 gitea_stats.py 2>&1 | tee -a /home/gitea/statics/gitea_stats.log
    exit_code=${PIPESTATUS[0]}
    if [ $exit_code -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S'): 手动执行成功" | tee -a /home/gitea/statics/cron.log
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S'): 手动执行失败，退出码: $exit_code" | tee -a /home/gitea/statics/cron.log
    fi
    exit $exit_code
fi

# 定时任务执行
echo "$(date '+%Y-%m-%d %H:%M:%S'): 定时任务开始执行" >> /home/gitea/statics/cron.log 2>&1

# 执行 Python 脚本
/usr/bin/python3 gitea_stats.py >> /home/gitea/statics/gitea_stats.log 2>&1

# 记录结束时间
echo "$(date '+%Y-%m-%d %H:%M:%S'): 定时任务执行完成" >> /home/gitea/statics/cron.log 2>&1

# 记录退出状态
if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): 定时任务执行成功" >> /home/gitea/statics/cron.log 2>&1
else
    echo "$(date '+%Y-%m-%d %H:%M:%S'): 定时任务执行失败，退出码: $?" >> /home/gitea/statics/cron.log 2>&1
fi