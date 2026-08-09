#!/bin/bash
# DraftBox 一键安装脚本
# 用法: curl -sSL https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.sh | bash

set -e

echo "🚀 DraftBox 安装中..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.8+"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "📦 安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# 创建目录
INSTALL_DIR="$HOME/.draftbox"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 下载项目
if [ ! -f "main.py" ]; then
    echo "📥 下载 DraftBox..."
    curl -sSL https://raw.githubusercontent.com/JCWD123/media_draftbox/master/draftbox_v2.tar.gz | tar xz
fi

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
if ! command -v wewrite &> /dev/null; then
    echo "📦 安装 wewrite..."
    pip install wewrite -q 2>/dev/null || pip install git+https://github.com/imraywang/wewrite.git -q
fi

# 安装前端依赖
echo "📦 安装前端依赖..."
cd web && npm install && cd ..

# 创建配置文件
if [ ! -f "config.yaml" ]; then
    cat > config.yaml << 'EOF'
model:
  api_key: ""
  base_url: "https://token-plan-cn.xiaomimimo.com/v1"
  model: "mimo-v2.5"
search:
  pexels_key: ""
  unsplash_key: ""
server:
  backend_port: 8502
  web_port: 3000
EOF
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 快速开始:"
echo "   1. 配置: python cli.py config init"
echo "   2. 启动: python start.sh"
echo "   3. 访问: http://localhost:3000"
echo ""
