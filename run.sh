#!/bin/bash
# ============================================
#   PSO数据分析工具 - 运行脚本 (Linux/macOS)
# ============================================

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  PSO数据分析工具"
echo "============================================"
echo ""

# 检查依赖是否安装
python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[提示] 首次运行或依赖缺失，正在检查..."
    python3 -m pip install -r requirements.txt >/dev/null 2>&1
fi

# 启动主程序
python3 main.py
