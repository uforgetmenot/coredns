#!/bin/bash
# Docker部署测试脚本

set -e

echo "🧪 Testing Docker deployment..."
echo ""

# 清理旧容器
echo "🧹 Cleaning up old containers..."
docker-compose down -v 2>/dev/null || true

# 确保Corefile存在
if [ ! -f data/Corefile ]; then
    echo "📄 Creating default Corefile..."
    cat > data/Corefile << 'EOF'
. {
    forward . 223.5.5.5
    log
    errors
}

example.com {
    hosts {
        192.168.1.1 www.example.com
        fallthrough
    }
    log
    errors
}
EOF
fi

# 构建并启动服务
echo "🐳 Building and starting containers..."
docker-compose up -d --build

# 等待服务启动
echo "⏳ Waiting for services to be healthy..."
sleep 10

# 检查容器状态
echo ""
echo "📊 Container status:"
docker-compose ps

# 测试健康检查
echo ""
echo "🏥 Testing health endpoints..."

# 测试Manager健康检查
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ CoreDNS Manager is healthy"
else
    echo "❌ CoreDNS Manager health check failed"
    docker-compose logs coredns-manager
    exit 1
fi

# 测试API文档
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ API docs accessible"
else
    echo "❌ API docs not accessible"
    exit 1
fi

# 检查数据库
echo ""
echo "💾 Checking database..."
if [ -f data/db/coredns.db ]; then
    echo "✅ Database file created"
    ls -lh data/db/coredns.db
else
    echo "❌ Database file not found"
    exit 1
fi

# 检查日志
echo ""
echo "📝 Recent logs:"
docker-compose logs --tail=10 coredns-manager

echo ""
echo "✅ All tests passed!"
echo ""
echo "🌐 Access points:"
echo "  - CoreDNS Manager: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Stop with: docker-compose down"
