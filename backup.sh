#!/bin/bash
# 试卷管理系统 - 数据备份脚本

set -e

# 配置
BACKUP_DIR="/var/backups/exam-system"
PROJECT_DIR="/var/www/exam-system"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "开始备份..."

# 备份数据库
if [ -f "$PROJECT_DIR/data/exam_system.db" ]; then
    cp "$PROJECT_DIR/data/exam_system.db" "$BACKUP_DIR/exam_$DATE.db"
    echo "✓ 数据库已备份: exam_$DATE.db"
else
    echo "✗ 数据库文件不存在"
fi

# 备份上传文件
if [ -d "$PROJECT_DIR/uploads" ]; then
    tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" -C "$PROJECT_DIR" uploads/
    echo "✓ 上传文件已备份: uploads_$DATE.tar.gz"
else
    echo "✗ 上传目录不存在"
fi

# 删除旧备份
find $BACKUP_DIR -mtime +$KEEP_DAYS -delete 2>/dev/null || true

echo "备份完成！"
echo "备份位置: $BACKUP_DIR"
ls -lh $BACKUP_DIR/*.db $BACKUP_DIR/*.tar.gz 2>/dev/null | tail -5
