#!/bin/bash

# CTOD 本地启动脚本
# 使用方式: ./start.sh [选项]

PORT=${CTOD_PORT:-5000}
LOG_LEVEL=${CTOD_LOGGING_LEVEL:-info}
CACHE_DIR=${CTOD_TILE_CACHE_PATH:-./ctod_cache}
DATASET_CONFIG=${CTOD_DATASET_CONFIG_PATH:-./config/datasets.json}

while [[ $# -gt 0 ]]; do
    case $1 in
        --port) PORT="$2"; shift 2 ;;
        --log-level) LOG_LEVEL="$2"; shift 2 ;;
        --cache-dir) CACHE_DIR="$2"; shift 2 ;;
        --dataset-config) DATASET_CONFIG="$2"; shift 2 ;;
        --no-cache) CACHE_DIR=""; shift ;;
        --no-dynamic) NO_DYNAMIC="--no-dynamic"; shift ;;
        --unsafe) UNSAFE="--unsafe"; shift ;;
        -h|--help)
            echo "用法: ./start.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --port PORT           服务端口 (默认: 5000)"
            echo "  --log-level LEVEL     日志级别: debug/info/warning/error (默认: info)"
            echo "  --cache-dir DIR       瓦片缓存目录 (默认: ./ctod_cache)"
            echo "  --no-cache            禁用缓存"
            echo "  --dataset-config PATH 数据集配置文件 (默认: ./config/datasets.json)"
            echo "  --no-dynamic          禁用动态端点，仅使用预配置数据集"
            echo "  --unsafe              加载不安全瓦片"
            echo ""
            echo "示例:"
            echo "  ./start.sh"
            echo "  ./start.sh --port 8080 --log-level debug"
            echo "  ./start.sh --no-dynamic --cache-dir /data/cache"
            exit 0
            ;;
        *) echo "未知选项: $1"; exit 1 ;;
    esac
done

CMD="poetry run start --port $PORT --logging-level $LOG_LEVEL --dataset-config $DATASET_CONFIG"

if [ -n "$CACHE_DIR" ]; then
    mkdir -p "$CACHE_DIR"
    CMD="$CMD --tile-cache-path $CACHE_DIR"
fi

[ -n "$NO_DYNAMIC" ] && CMD="$CMD $NO_DYNAMIC"
[ -n "$UNSAFE" ] && CMD="$CMD $UNSAFE"

echo "启动 CTOD 服务..."
echo "  端口: $PORT"
echo "  日志级别: $LOG_LEVEL"
echo "  缓存目录: ${CACHE_DIR:-禁用}"
echo "  数据集配置: $DATASET_CONFIG"
echo ""
echo "访问地址:"
echo "  首页:            http://localhost:$PORT"
echo "  API 文档:        http://localhost:$PORT/docs"
echo "  动态 layer.json: http://localhost:$PORT/tiles/dynamic/layer.json?cog=/path/to/your.tif"
echo ""

exec $CMD
