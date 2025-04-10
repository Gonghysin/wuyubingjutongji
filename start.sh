#!/bin/bash

# 确保日志目录存在
mkdir -p logs

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 杀死可能已存在的进程
pkill -f "python3 $SCRIPT_DIR/run.py --port=8080"

# 在后台启动应用，指定端口为8080，将输出重定向到日志文件
echo "正在启动服务..."
nohup python3 "$SCRIPT_DIR/run.py" --port=8080 > "$SCRIPT_DIR/logs/app.log" 2>&1 &

# 将进程ID保存到文件中，以便稍后可以停止服务
echo $! > "$SCRIPT_DIR/app.pid"
echo "服务已在8080端口启动，进程ID: $(cat "$SCRIPT_DIR/app.pid")"
echo "日志文件位置: $SCRIPT_DIR/logs/app.log"
echo "查看日志请执行: tail -f $SCRIPT_DIR/logs/app.log"