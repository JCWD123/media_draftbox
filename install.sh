#!/bin/bash
# DraftBox 一键安装脚本
# Linux/macOS: curl -fsSL https://raw.githubusercontent.com/JCWD123/media_draftbox/master/install.sh | bash

set -e

echo "🚀 DraftBox 安装中..."

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
    git fetch --depth 1 origin master -q
    git checkout FETCH_HEAD -q
    cd -
fi

# 安装 Python 依赖
echo "📦 安装依赖..."
pip install fastapi uvicorn pyyaml requests markdown beautifulsoup4 Pillow -q

# 安装 wewrite
if ! command -v wewrite &> /dev/null; then
    pip install wewrite -q 2>/dev/null || true
fi

# 创建 draftbox 命令（参考 hermes-agent 做法）
echo "🔧 创建 draftbox 命令..."

# Linux/macOS: 创建符号链接到用户目录的 bin
if [ -d "$HOME/.local/bin" ]; then
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/draftbox" << 'COMMAND'
#!/bin/bash
cd ~/.draftbox
python cli.py "$@"
COMMAND
    chmod +x "$HOME/.local/bin/draftbox"
    
    # 添加到 PATH（如果还没有）
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        export PATH="$HOME/.local/bin:$PATH"
        echo "✅ 已添加 ~/.local/bin 到 PATH"
    fi
fi

# macOS: 添加到 zshrc
if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q ".local/bin" "$HOME/.zshrc" 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 使用方法（重启终端后生效）："
echo "   draftbox setup    # 配置向导"
echo "   draftbox model    # 模型配置"
echo "   draftbox start    # 启动服务"
echo ""

# 立即执行 setup
cd "$INSTALL_DIR"
python cli.py setup
