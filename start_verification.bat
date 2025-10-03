@echo off
echo ========================================
echo AIME题目人工验证系统
echo ========================================
echo.

REM 激活conda环境
call conda activate camel

REM 检查gradio是否安装
python -c "import gradio" 2>nul
if errorlevel 1 (
    echo [安装] 正在安装gradio...
    pip install gradio
)

echo [启动] 正在启动验证UI...
echo.
echo 请在浏览器中访问: http://127.0.0.1:7860
echo.
echo 按 Ctrl+C 停止服务器
echo.

python verification_ui.py

pause

