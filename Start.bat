@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动服务器...
start "游戏服务器" cmd /k python "server.py"
ping -n 3 127.0.0.1 >nul
echo 正在启动客户端...
start "游戏客户端" cmd /k python "client.py"
echo 所有窗口已启动，请分别操作。
pause