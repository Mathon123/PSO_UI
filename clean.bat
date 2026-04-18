@echo off
chcp 65001 > nul
echo ========================================
echo PSO_UI 清理脚本
echo ========================================
echo.

echo [1/4] 清理Python缓存文件...
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo   已清理 __pycache__
)

echo.
echo [2/4] 清理.pyc文件...
for /r %%i in (*.pyc) do (
    del /q "%%i" 2>nul
)
echo   已清理 *.pyc 文件

echo.
echo [3/4] 清理pytest缓存...
if exist ".pytest_cache" (
    rmdir /s /q ".pytest_cache"
    echo   已清理 .pytest_cache
)

echo.
echo [4/4] 清理临时文件...
if exist "*.tmp" (
    del /q "*.tmp" 2>nul
    echo   已清理 *.tmp 文件
)
if exist "*.log" (
    del /q "*.log" 2>nul
    echo   已清理 *.log 文件
)

echo.
echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 注意: 用户数据文件(data/, output/)未被清理
echo       如需完全清理，请手动删除这些目录
echo.
pause
