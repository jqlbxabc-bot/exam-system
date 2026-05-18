#!/bin/bash
# 试卷管理系统 - 服务监控脚本

# 配置
SERVICE_NAME="exam-system"
CHECK_URL="http://localhost:5001"
LOG_FILE="/var/log/exam-system-monitor.log"

# 检查服务状态
check_service() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        return 0
    else
        return 1
    fi
}

# 检查HTTP响应
check_http() {
    if curl -s -f -o /dev/null $CHECK_URL; then
        return 0
    else
        return 1
    fi
}

# 记录日志
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> $LOG_FILE
}

# 主逻辑
if ! check_service; then
    log "服务未运行，正在重启..."
    systemctl restart $SERVICE_NAME
    sleep 5
    if check_service; then
        log "服务重启成功"
    else
        log "服务重启失败！"
    fi
elif ! check_http; then
    log "HTTP检查失败，正在重启服务..."
    systemctl restart $SERVICE_NAME
    sleep 5
    if check_http; then
        log "服务重启成功"
    else
        log "服务重启失败！"
    fi
fi
