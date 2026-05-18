#!/bin/bash
# 试卷管理系统 - 一键部署脚本

set -e

echo "========================================"
echo "  试卷管理系统 - 一键部署"
echo "========================================"
echo

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用root用户运行此脚本"
    echo "sudo bash deploy.sh"
    exit 1
fi

# 获取配置
read -p "请输入域名（直接回车使用IP）: " DOMAIN
read -p "请输入端口（默认5001）: " PORT
PORT=${PORT:-5001}

echo
echo "[1/8] 更新系统..."
apt update && apt upgrade -y

echo
echo "[2/8] 安装依赖..."
apt install python3 python3-pip python3-venv nginx -y

echo
echo "[3/8] 创建项目目录..."
mkdir -p /var/www/exam-system
cd /var/www/exam-system

echo
echo "[4/8] 上传项目文件..."
echo "请将项目文件上传到 /var/www/exam-system 目录"
echo "可以使用以下命令："
echo "scp -r ./* root@服务器IP:/var/www/exam-system/"
read -p "文件上传完成后按回车继续..."

echo
echo "[5/8] 配置Python环境..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

echo
echo "[6/8] 初始化数据库..."
python -c "import database; database.init_db()"

echo
echo "[7/8] 配置系统服务..."
cat > /etc/systemd/system/exam-system.service << EOF
[Unit]
Description=Exam System
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/exam-system
Environment="PATH=/var/www/exam-system/venv/bin"
ExecStart=/var/www/exam-system/venv/bin/gunicorn -b 127.0.0.1:$PORT -w 4 --timeout 120 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
chown -R www-data:www-data /var/www/exam-system
chmod -R 755 /var/www/exam-system

systemctl daemon-reload
systemctl enable exam-system
systemctl start exam-system

echo
echo "[8/8] 配置Nginx..."
if [ -z "$DOMAIN" ]; then
    SERVER_NAME="_"
else
    SERVER_NAME="$DOMAIN"
fi

cat > /etc/nginx/sites-available/exam-system << EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /uploads {
        alias /var/www/exam-system/uploads;
    }

    client_max_body_size 100M;
}
EOF

ln -sf /etc/nginx/sites-available/exam-system /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

echo
echo "========================================"
echo "  部署完成！"
echo "========================================"
echo
echo "访问地址: http://${DOMAIN:-服务器IP}"
echo "默认账号: admin / admin123"
echo
echo "常用命令："
echo "  查看状态: systemctl status exam-system"
echo "  查看日志: journalctl -u exam-system -f"
echo "  重启服务: systemctl restart exam-system"
echo "  停止服务: systemctl stop exam-system"
echo
echo "数据备份："
echo "  数据库: /var/www/exam-system/data/exam_system.db"
echo "  上传文件: /var/www/exam-system/uploads/"
echo
