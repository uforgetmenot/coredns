#!/bin/bash
set -e

echo "🚀 Starting CoreDNS Manager..."
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# 创建必要的目录
echo "📁 Creating necessary directories..."
mkdir -p data/db

# 检查 Corefile 是否存在
if [ ! -f "data/Corefile" ]; then
    echo "❌ data/Corefile not found!"
    echo "Please copy your Corefile to data/Corefile or run:"
    echo "  cp docker/Corefile data/Corefile"
    exit 1
fi

echo "✅ Corefile found"
echo ""

# 启动服务
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Container status:"
docker-compose ps
echo ""
echo "🌐 Access the following URLs:"
echo "  - CoreDNS Manager: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "📝 View logs with:"
echo "  docker-compose logs -f"
echo ""
echo "🛑 Stop services with:"
echo "  docker-compose down"
