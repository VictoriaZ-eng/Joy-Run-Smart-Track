@echo off
REM 创建名为 joyrun-py311 的 conda 环境，指定 Python 3.11
conda create -y -n joyrun-py311 python=3.11

REM 用 conda run 在新环境下安装 requirements.txt 中的依赖
conda run -n joyrun-py311 pip install -r requirements.txt

echo 环境创建并安装 Flask 完成！
pause
