#!/bin/bash
# DraftBox 启动脚本

echo "🚀 启动 DraftBox..."

# 启动后端
echo "📡 启动后端 (端口 8502)..."
cd backend && python -m uvicorn main:app --port 8502 --host 0.0.0.0 &
BACKEND_PID=$!

# 启动前端
echo "🎨 启动前端..."
cd ../web && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ DraftBox 已启动！"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8502"
echo "   API文档: http://localhost:8502/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待退出
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
