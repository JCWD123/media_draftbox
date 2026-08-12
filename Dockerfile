# DraftBox 单容器镜像（前后端同容器）
# 国内加速: 可把 python:3.11-slim 换成 docker.m.daocloud.io/library/python:3.11-slim 等国内镜像
FROM python:3.11-slim

# 国内 apt 源加速（可选，可注释）
RUN printf 'deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free\ndeb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free\n' > /etc/apt/sources.list \
  && sed -i 's/https:/http:/' /etc/apt/sources.list 2>/dev/null || true

# 安装 node/npm（前端 vite 需要，用 apt）
RUN apt-get update -qq \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl nodejs npm git > /dev/null \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制项目
COPY . .

# 后端依赖（国内 pip 镜像加速）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ 2>/dev/null; \
    pip install --no-cache-dir fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow feedparser wewrite

# 前端依赖（国内 npm 镜像加速）
WORKDIR /app/web
RUN npm config set registry https://registry.npmmirror.com/ 2>/dev/null; \
    npm install
WORKDIR /app

# 暴露端口：前端 3000，后端 8502
EXPOSE 3000 8502

# 启动前后端（后端 uvicorn + 前端 vite）
CMD ["sh", "-c", "cd /app/backend && python -m uvicorn main:app --port 8502 --host 0.0.0.0 & cd /app/web && npm run dev -- --host 0.0.0.0"]
