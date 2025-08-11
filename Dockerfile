FROM python:3.11-slim

WORKDIR /app

# 切换到更可靠的镜像源并安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制源代码
COPY src/ ./src/
COPY qimenEngine/ ./qimenEngine/
COPY scripts/ ./scripts/
COPY alembic.ini .
COPY alembic/ ./alembic/

# 创建非 root 用户
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 