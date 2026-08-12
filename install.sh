#!/bin/bash
# DraftBox 一键安装脚本
# Linux/macOS: curl -fsSL https://raw.githubusercontent.com/JCWD123/media_draftbox/main/install.sh | bash

set -e

echo "🚀 DraftBox 安装中..."

# 检测 Python 命令（兼容 python3 / python 两种命名）
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ 未找到 python/python3，请先安装 Python 3" >&2
    exit 1
fi
echo "  使用 Python: $PYTHON"

INSTALL_DIR="$HOME/.draftbox"

# 清理不完整目录
if [ -d "$INSTALL_DIR" ] && [ ! -f "$INSTALL_DIR/cli.py" ]; then
    echo "🔄 清理旧文件..."
    rm -rf "$INSTALL_DIR"
fi

# 克隆项目
if [ ! -f "$INSTALL_DIR/cli.py" ]; then
    echo "📥 下载 DraftBox..."
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    git init -q
    git remote add origin https://github.com/JCWD123/media_draftbox.git
    git fetch --depth 1 origin main -q
    git checkout FETCH_HEAD -q
    cd -
fi

# 安装 Python 依赖
echo "📦 安装依赖..."
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow feedparser -q

# 安装 wewrite
if ! command -v wewrite &> /dev/null; then
    pip install wewrite -q 2>/dev/null || true
fi

# 安装前端依赖
echo "📦 安装前端依赖..."
if [ -f "$INSTALL_DIR/web/package.json" ]; then
    cd "$INSTALL_DIR/web" && npm install && cd -
    echo "  ✅ 前端依赖安装完成"
fi

# 创建 draftbox 命令
echo "🔧 创建 draftbox 命令..."

# 创建 ~/.local/bin 目录（如果不存在）
mkdir -p "$HOME/.local/bin"

# 创建 draftbox 脚本
cat > "$HOME/.local/bin/draftbox" << 'COMMAND'
#!/bin/bash
# 运行时检测 python 命令（兼容 python3/python）
if command -v python3 &> /dev/null; then PY=python3; else PY=python; fi
cd ~/.draftbox
exec "$PY" cli.py "$@"
COMMAND
chmod +x "$HOME/.local/bin/draftbox"
echo "  ✅ 已创建 ~/.local/bin/draftbox"

# 添加到 ~/.bashrc（永久保存）
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "  ✅ 已添加到 ~/.bashrc（永久保存）"
fi

# macOS: 添加到 ~/.zshrc
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q ".local/bin" "$HOME/.zshrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
        echo "  ✅ 已添加到 ~/.zshrc（永久保存）"
    fi
fi

# 更新当前会话 PATH（立即生效）
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 使用方法（重启终端后永久生效）："
echo "   draftbox setup    # 配置向导"
echo "   draftbox model    # 模型配置"
echo "   draftbox start    # 启动服务"
echo ""

# 立即执行 setup
cd "$INSTALL_DIR"
$PYTHON cli.py setup
