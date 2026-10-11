#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  JiuZhang 持续训练管理脚本 (MLX LoRA)
#  专为 Apple MacBook Air M4 16GB 后台运行设计
#
#  特性:
#   • nice -n 20  最低 CPU 优先级，绝不抢占前台应用
#   • nohup       终端断开后仍继续运行
#   • SIGTERM     安全暂停，保存当前检查点后退出
#
#  依赖: python3 mlx-lm transformers datasets
#
#  用法:
#    bash run.sh start           # 首次后台启动
#    bash run.sh resume         # 从断点恢复
#    bash run.sh status          # 查看运行状态
#    bash run.sh log             # 实时滚动日志
#    bash run.sh stop            # 安全停止 (先保存再退出)
#    bash run.sh quick           # 快速测试 (1 epoch, ~5 min)
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

# ── 配置 ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/jiuzhang-math/bin/python"
OUTPUT="${SCRIPT_DIR}/outputs"
LOG="${OUTPUT}/training.log"
PID_FILE="${OUTPUT}/.pid"

# 找不到 venv 就用系统 python3
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

# ── 颜色 ──
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

help() {
    echo -e "${CYAN}JiuZhang MLX LoRA 持续训练管理器${NC}"
    echo ""
    echo "用法: bash $0 <命令>"
    echo ""
    echo "  ${GREEN}start${NC}    首次后台启动 (nice 最低优先级)"
    echo "  ${GREEN}resume${NC}   恢复中断的训练"
    echo "  ${GREEN}quick${NC}    快速验证: 1 epoch, ~5 分钟"
    echo "  ${YELLOW}status${NC}   查看进程状态与进度"
    echo "  ${YELLOW}log${NC}      实时滚动日志 (Ctrl+C 退出)"
    echo "  ${RED}stop${NC}     发送 SIGTERM, 安全保存后停止"
    echo ""
    echo "后台训练时: 前台操作完全不受影响。"
}

ensure_output() {
    mkdir -p "$OUTPUT"
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

cmd_start() {
    if is_running; then
        echo -e "${YELLOW}⚠️  已在运行 (PID=$(cat "$PID_FILE"))${NC}"
        echo "   查看日志: bash $0 log"
        return 1
    fi

    ensure_output
    echo -e "${GREEN}🚀 启动后台训练 (nice 20 + nohup)...${NC}"
    echo "   输出: $OUTPUT"
    echo "   日志: $LOG"
    echo ""

    # nice -n 20 : 最低 CPU 时间片优先级
    # exec 使 nice 直接替换为 python，PID 即 python PID
    # nohup + trap HUP : 终端退出时不终止
    nohup nice -n 20 "$PYTHON" "${SCRIPT_DIR}/scripts/train_mlx_lora.py" \
        --epochs 5 \
        --batch-size 1 \
        --grad-accum 8 \
        --lora-r 4 \
        --max-seq 256 \
        --lr 8e-5 \
        --steps-save 100 \
        --output "$OUTPUT/jiuzhang-math-0.8b" \
        >> "$LOG" 2>&1 &

    local PID=$!
    echo $PID > "$PID_FILE"
    disown "$PID" 2>/dev/null || true

    echo -e "${GREEN}✅ 进程 PID = $PID${NC}"
    echo ""
    echo "   常用命令:"
    echo "     bash $0 log"
    echo "     bash $0 status"
    echo "     bash $0 stop"
    sleep 2
}

cmd_resume() {
    echo -e "${CYAN}🔄 恢复训练...${NC}"
    if is_running; then
        echo -e "${YELLOW}⚠️  已在运行，无需恢复${NC}"
        return 1
    fi

    ensure_output
    nohup nice -n 20 "$PYTHON" "${SCRIPT_DIR}/scripts/train_mlx_lora.py" \
        --resume \
        --epochs 5 \
        --batch-size 1 \
        --grad-accum 8 \
        --lora-r 4 \
        --max-seq 256 \
        --lr 8e-5 \
        --steps-save 100 \
        --output "$OUTPUT/jiuzhang-math-0.8b" \
        >> "$LOG" 2>&1 &

    local PID=$!
    echo $PID > "$PID_FILE"
    disown "$PID" 2>/dev/null || true
    echo -e "${GREEN}✅ 恢复 PID = $PID${NC}"
}

cmd_quick() {
    echo -e "${CYAN}⚡ 快速验证启动 (1 epoch, ~5 min)...${NC}"
    ensure_output

    # 直接前台运行，以便观察
    "$PYTHON" "${SCRIPT_DIR}/scripts/train_mlx_lora.py" \
        --epochs 1 \
        --batch-size 1 \
        --grad-accum 4 \
        --lora-r 2 \
        --max-seq 128 \
        --lr 1e-4 \
        --steps-save 20 \
        --steps-eval 50 \
        --output "$OUTPUT/jiuzhang-math-quick"
}

cmd_status() {
    echo -e "${CYAN}📊 运行状态${NC}"
    echo ""

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  进程状态: ${GREEN}运行中${NC} (PID=$pid)"
            echo "  CPU 占用: $(ps -p "$pid" -o %cpu= 2>/dev/null) %"
            echo "  内存占用: $(ps -p "$pid" -o %mem= 2>/dev/null) %"
            echo "  运行时间: $(ps -p "$pid" -o etime= 2>/dev/null)"
        else
            echo "  进程状态: ${RED}已退出${NC} (PID=$pid)"
            rm -f "$PID_FILE"
        fi
    else
        echo "  进程状态: ${YELLOW}未启动${NC}"
    fi

    if [ -f "$LOG" ]; then
        echo ""
        echo "  最新日志 (最后10行):"
        tail -n 10 "$LOG" | sed 's/^/    /'
    fi

    if [ -d "$OUTPUT/jiuzhang-math-0.8b" ]; then
        local adapters="$OUTPUT/jiuzhang-math-0.8b/adapters.safetensors"
        if [ -f "$adapters" ]; then
            local size_kb=$(stat -f%z "$adapters" 2>/dev/null || stat -c%s "$adapters" 2>/dev/null)
            echo ""
            echo "  LoRA 适配器大小: $((size_kb / 1024)) KB"
        fi
    fi
}

cmd_log() {
    if [ ! -f "$LOG" ]; then
        echo -e "${RED}❌ 日志文件不存在: $LOG${NC}"
        return 1
    fi
    echo -e "${CYAN}📜 滚动日志 (Ctrl+C 退出):${NC}"
    tail -f "$LOG"
}

cmd_stop() {
    if ! is_running; then
        echo -e "${YELLOW}⚠️  进程未在运行${NC}"
        rm -f "$PID_FILE"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    echo -e "${YELLOW}🛑 发送 SIGTERM 到 PID=$pid...${NC}"
    echo "   (训练进程将在当前 step 保存检查点后退出)"
    kill -TERM "$pid"

    echo "   等待退出..."
    for i in {1..30}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo -e "\n${GREEN}✅ 已成功优雅退出${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        echo -n "   ."
        sleep 2
    done

    echo -e "\n${RED}⚠️  进程在 60s 内未退出，强制终止...${NC}"
    kill -KILL "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
}

# ── 主入口 ──
CMD="${1:-help}"
shift || true

case "$CMD" in
    start)   cmd_start ;;
    resume)  cmd_resume ;;
    quick)   cmd_quick ;;
    status)  cmd_status ;;
    log)     cmd_log ;;
    stop)    cmd_stop ;;
    *)       help ;;
esac
