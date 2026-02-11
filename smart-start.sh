#!/bin/bash

echo "=== Xray-Sing 智能启动脚本 ==="
echo ""

# 停止现有服务
echo "1. 停止现有服务..."
pkill -f "java.*server.jar" 2>/dev/null
pkill -f sing-box 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 3

# 检查端口可用性的函数
check_port() {
    local port=$1
    if command -v nc &> /dev/null; then
        nc -z 127.0.0.1 $port 2>/dev/null
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -tuln | grep -q ":$port "
        return $?
    else
        # 使用 /dev/tcp 检查
        (echo >/dev/tcp/127.0.0.1/$port) 2>/dev/null
        return $?
    fi
}

# 查找可用端口
find_available_port() {
    local ports=("$@")
    for port in "${ports[@]}"; do
        if ! check_port $port; then
            echo $port
            return 0
        fi
    done
    return 1
}

# 候选端口列表
CANDIDATE_PORTS=(${SERVER_PORT:-8688} 25565 25566 25567 30000 30001 19132 8080 8081)

echo "2. 检查可用端口..."
echo "   候选端口: ${CANDIDATE_PORTS[*]}"

AVAILABLE_PORT=$(find_available_port "${CANDIDATE_PORTS[@]}")

if [ -z "$AVAILABLE_PORT" ]; then
    echo "❌ 错误：没有找到可用端口！"
    echo "   请在 Pterodactyl 面板中分配更多端口。"
    exit 1
fi

echo "✅ 找到可用端口: $AVAILABLE_PORT"
echo ""

# 自动获取公网 IP
echo "3. 获取服务器信息..."
PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || curl -s --max-time 5 api.ipify.org 2>/dev/null || echo "未知")
HOSTNAME=$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo "localhost")

echo "   服务器地址: $HOSTNAME"
echo "   公网 IP: $PUBLIC_IP"
echo ""

# 设置环境变量
export SB_PORT=$AVAILABLE_PORT
export PORT=$AVAILABLE_PORT
export ARGO_PORT=$AVAILABLE_PORT
export SUB_PATH="${SUB_PATH:-zmm}"
export FILE_PATH="${FILE_PATH:-/tmp/.cache}"

# 显示配置
echo "4. 启动配置:"
echo "   ├─ Hysteria2 端口: $SB_PORT (UDP)"
echo "   ├─ HTTP 订阅端口: $PORT (TCP)"
echo "   ├─ Xray 内部端口: $ARGO_PORT"
echo "   ├─ 订阅路径: /$SUB_PATH"
echo "   └─ 数据目录: $FILE_PATH"
echo ""

# 显示访问地址
echo "5. 访问地址:"
if [ "$HOSTNAME" != "localhost" ]; then
    echo "   ├─ 订阅页面: http://$HOSTNAME:$PORT/$SUB_PATH"
fi
if [ "$PUBLIC_IP" != "未知" ]; then
    echo "   └─ 订阅页面: http://$PUBLIC_IP:$PORT/$SUB_PATH"
fi
echo ""

echo "=== 启动服务 ==="
echo ""

# 启动服务
java -jar server.jar

# 如果启动失败
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 服务启动失败！"
    echo "   请检查 server.jar 文件是否存在。"
    exit 1
fi
