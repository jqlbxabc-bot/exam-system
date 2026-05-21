FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖（包括 OCR 和 .doc 文档提取工具）
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    antiword \
    catdoc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .
RUN mkdir -p data uploads/exams logs
RUN chmod +x start.sh

EXPOSE 80

CMD ["python", "run.py"]
