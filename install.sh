#!/bin/bash
# DraftBox 一键安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.sh | bash

set -e

echo "🚀 DraftBox 安装中..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.8+"
    exit 1
fi

# 安装目录
INSTALL_DIR="$HOME/.draftbox"
mkdir -p "$INSTALL_DIR"

# 下载项目
if [ ! -f "$INSTALL_DIR/cli.py" ]; then
    echo "📥 下载 DraftBox..."
    cd /tmp
    curl -sSL https://raw.githubusercontent.com/JCWD123/media_draftbox/master/draftbox_v2.tar.gz -o draftbox.tar.gz
    tar xzf draftbox.tar.gz -C "$INSTALL_DIR"
    rm draftbox.tar.gz
fi

# 安装 Python 依赖
echo "📦 安装依赖..."
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
if ! command -v wewrite &> /dev/null; then
    pip install wewrite -q 2>/dev/null || pip install git+https://github.com/imraywang/wewrite.git -q
fi

# 创建全局命令 draftbox
cat > /usr/local/bin/draftbox << 'COMMAND'
#!/bin/bash
cd ~/.draftbox
python cli.py "$@"
COMMAND
chmod +x /usr/local/bin/draftbox 2>/dev/null || sudo chmod +x /usr/local/bin/draftbox

# Windows 兼容
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    cat > ~/draftbox.cmd << 'COMMAND'
@echo off
cd %USERPROFILE%\.draftbox
python cli.py %*
COMMAND
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 开始使用:"
echo "   draftbox setup    # 配置向导"
echo ""
