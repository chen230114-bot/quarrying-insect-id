# Dockerfile - 昆虫识别项目容器化
FROM docker.1ms.run/python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --timeout=600 --retries=5

RUN pip install --no-cache-dir -r requirements.txt \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --timeout=600 --retries=5

# 创建模型和图片目录
RUN mkdir -p models images

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["python", "demo.py"]