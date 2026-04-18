@echo off
chcp 65001 > nul
echo ========================================
echo PSO_UI 依赖安装脚本
echo ========================================
echo.

echo [1/3] 检查Python版本...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 升级pip...
python -m pip install --upgrade pip

echo.
echo [3/3] 安装项目依赖...
pip install -r requirements.txt

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 可选：安装开发依赖（测试、文档工具）
echo   pip install -r requirements-dev.txt
echo.
echo 可选：安装全部依赖（包括开发依赖）
echo   pip install pso-ui[all]
echo.
pause
