# ===== 阶段1：构建前端 =====
FROM node:18-alpine AS frontend-builder
WORKDIR /build/client
COPY client/package*.json ./
RUN npm ci --production=false
COPY client/ ./
RUN npm run build

# ===== 阶段2：运行后端 =====
FROM python:3.12-slim
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir tornado pytest

# 拷贝后端代码
COPY server/ ./server/

# 拷贝前端构建产物
COPY --from=frontend-builder /build/client/dist ./client/dist

# 数据目录（SQLite 持久化）
RUN mkdir -p /app/data

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV EXPERIMENT_DB_PATH=/app/data/experiment.sqlite3
ENV PORT=8888
ENV CLIENT_DIST_PATH=/app/client/dist

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8888/api/participants || exit 1

CMD ["python3", "server/server.py"]
