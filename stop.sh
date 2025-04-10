#!/bin/bash

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查PID文件是否存在
if [ ! -f "$SCRIPT_DIR/app.pid" ]; then
    echo "服务未运行或PID文件不存在"
    exit 1
fi

# 从PID文件读取进程ID
PID=$(cat "$SCRIPT_DIR/app.pid")

# 检查进程是否存在
if ! ps -p $PID > /dev/null; then
    echo "进程 $PID 不存在，可能服务已经停止"
    rm -f "$SCRIPT_DIR/app.pid"
    exit 1
fi

echo "正在停止服务，进程ID: $PID..."

# 杀死进程
kill $PID

# 等待进程终止
for i in {1..10}; do
    if ! ps -p $PID > /dev/null; then
        echo "服务已成功停止"
        rm -f "$SCRIPT_DIR/app.pid"
        echo "查看服务日志请执行: cat $SCRIPT_DIR/logs/app.log"
        exit 0
    fi
    sleep 1
done

# 如果进程未能在指定时间内终止，强制终止
echo "服务未能正常停止，正在强制终止..."
kill -9 $PID
echo "服务已强制停止"
rm -f "$SCRIPT_DIR/app.pid"
echo "查看服务日志请执行: cat $SCRIPT_DIR/logs/app.log"