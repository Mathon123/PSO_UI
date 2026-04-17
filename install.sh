#!/bin/bash
# ============================================
#   PSO数据分析工具 - 安装脚本 (Linux/macOS)
# ============================================

set -e  # 遇到错误立即退出

echo "============================================"
echo "  PSO数据分析工具 - 安装脚本"
echo "============================================"
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8或更高版本"
    echo "下载地址: https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] 检查Python版本..."
python3 --version
echo ""

echo "[2/4] 升级pip..."
python3 -m pip install --upgrade pip
echo ""

echo "[3/4] 安装依赖包..."
python3 -m pip install -r requirements.txt
echo ""

echo "[4/4] 验证安装..."
python3 -c "import PyQt6; import numpy; import scipy; import pandas; import matplotlib; print('所有依赖包安装成功!')"
echo ""

echo "============================================"
echo "  安装完成!"
echo "============================================"
echo ""
echo "运行程序: ./run.sh"
echo ""
