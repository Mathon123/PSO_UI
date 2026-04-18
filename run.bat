@echo off
chcp 65001 > nul
echo ========================================
echo PSO_UI 启动脚本
echo ========================================
echo.

echo 正在启动PSO数据分析工具...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo 启动失败，请检查错误信息。
    pause
)
