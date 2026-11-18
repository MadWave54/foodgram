@echo off
cd /d "%~dp0infra"
if not exist .env copy .env.example .env >nul
docker compose up -d --build
if errorlevel 1 goto error
docker compose exec -T backend python manage.py seed_demo
if errorlevel 1 goto error
start http://localhost:8080
exit /b 0
:error
echo Foodgram failed to start. Check Docker Desktop and the output above.
pause
exit /b 1
