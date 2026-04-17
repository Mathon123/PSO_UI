@echo off
chcp 65001 >nul
echo ============================================
echo   PSO数据分析工具
echo ============================================
echo.

:: 启动主程序
python main.py

:: 如果出错，显示错误信息
if errorlevel 1 (
    echo.
    echo [错误] 程序启动失败
    echo.
    echo 请确保已运行 install.bat 安装依赖
    echo.
    pause
)
