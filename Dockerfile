FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p data uploads/exams logs

# 启动脚本
RUN chmod +x start.sh

CMD ["./start.sh"]
