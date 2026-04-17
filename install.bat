@echo off
chcp 65001 >nul
echo ============================================
echo   PSO数据分析工具 - 安装脚本
echo ============================================
echo.

:: 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查Python版本...
python --version
echo.

echo [2/4] 升级pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [警告] pip升级失败，继续安装...
)
echo.

echo [3/4] 安装依赖包...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo.

echo [4/4] 验证安装...
python -c "import PyQt6; import numpy; import scipy; import pandas; import matplotlib; print('所有依赖包安装成功!')"
if errorlevel 1 (
    echo [错误] 依赖验证失败
    pause
    exit /b 1
)
echo.

echo ============================================
echo   安装完成!
echo ============================================
echo.
echo 运行程序: run.bat
echo.
pause
