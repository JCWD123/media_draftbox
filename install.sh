#!/bin/bash
# DraftBox 一键安装脚本
# Linux/macOS: curl -fsSL https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.sh | bash

set -e

echo "🚀 DraftBox 安装中..."

# 安装目录
INSTALL_DIR="$HOME/.draftbox"

# 如果目录已存在但不完整，先删除
if [ -d "$INSTALL_DIR" ] && [ ! -f "$INSTALL_DIR/cli.py" ]; then
    echo "🔄 清理旧文件..."
    rm -rf "$INSTALL_DIR"
fi

# 克隆项目
if [ ! -f "$INSTALL_DIR/cli.py" ]; then
    echo "📥 下载 DraftBox..."
    git clone --depth 1 https://github.com/JCWD123/media_draftbox.git "$INSTALL_DIR"
fi

# 安装 Python 依赖
echo "📦 安装依赖..."
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
if ! command -v wewrite &> /dev/null; then
    pip install wewrite -q 2>/dev/null || pip install git+https://github.com/imraywang/wewrite.git -q
fi

# 创建全局命令
cat > /usr/local/bin/draftbox << 'COMMAND'
#!/bin/bash
cd ~/.draftbox
python cli.py "$@"
COMMAND
chmod +x /usr/local/bin/draftbox 2>/dev/null || sudo chmod +x /usr/local/bin/draftbox

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 立即可用："
echo "   draftbox setup    # 配置向导"
echo ""

# 立即执行 setup
draftbox setup
