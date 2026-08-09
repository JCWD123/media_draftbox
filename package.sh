#!/bin/bash
# DraftBox 打包脚本

echo "📦 打包 DraftBox..."

# 打包前端
echo "🔨 构建前端..."
cd web && npm run build && cd ..

# 创建发布包
VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")
PACKAGE="draftbox-v${VERSION}.tar.gz"

echo "📦 创建 ${PACKAGE}..."
tar czf "${PACKAGE}" \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    backend/ \
    web/dist/ \
    src/ \
    cli.py \
    start.sh \
    install.sh \
    config.yaml \
    README.md \
    LICENSE

echo "✅ 打包完成: ${PACKAGE}"
echo "   大小: $(du -h ${PACKAGE} | cut -f1)"
