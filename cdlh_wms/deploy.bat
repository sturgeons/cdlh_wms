@echo off
chcp 65001
setlocal enabledelayedexpansion

:: 设置变量
set SERVER_IP=mgn.delink.top
set SERVER_USER=root
set REMOTE_PATH=/root/cdlh_wms
set LOCAL_PATH=%~dp0

:: 创建requirements.txt
echo 正在生成requirements.txt...
pip freeze > requirements.txt

:: 创建.gitignore
echo 正在创建.gitignore...
(
echo __pycache__/
echo *.pyc
echo *.pyo
echo *.pyd
echo .Python
echo env/
echo venv/
echo .env
echo .venv
echo db.sqlite3
echo .idea/
echo .vscode/
) > .gitignore

:: 创建部署包
echo 正在创建部署包...
if exist deploy.zip del deploy.zip
powershell Compress-Archive -Path "jssp","template","cdlh_wms","manage.py","requirements.txt" -DestinationPath "deploy.zip" -Force

:: 在服务器上创建目录
echo 正在在服务器上创建目录...
ssh %SERVER_USER%@%SERVER_IP% "mkdir -p %REMOTE_PATH%"

:: 上传到服务器
echo 正在上传到服务器...
scp deploy.zip %SERVER_USER%@%SERVER_IP%:%REMOTE_PATH%/

:: 在服务器上执行部署命令
echo 正在在服务器上部署...
ssh %SERVER_USER%@%SERVER_IP% "cd %REMOTE_PATH% && unzip -o deploy.zip && rm deploy.zip && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python manage.py migrate && sudo systemctl restart gunicorn"

echo 部署完成！
pause 