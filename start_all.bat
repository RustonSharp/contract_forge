@echo off
REM Contract Forge - 一键启动所有服务（Windows）

echo ======================================================================
echo 🚀 Contract Forge - 一键启动所有服务
echo ======================================================================
echo.

echo 1️⃣  启动数据库...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Docker 启动失败，请确保 Docker Desktop 正在运行
    pause
    exit /b 1
)

timeout /t 3 >nul
echo ✅ 数据库已启动
echo.

echo 2️⃣  启动后端 API...
start "Contract Forge - Backend" cmd /k python main.py

timeout /t 2 >nul
echo ✅ 后端已启动（新窗口）
echo.

echo 3️⃣  启动前端...
cd frontend
start "Contract Forge - Frontend" cmd /k npm run dev
cd ..

echo.
echo ======================================================================
echo ✅ 所有服务已启动！
echo ======================================================================
echo.
echo 📊 服务地址:
echo   - 前端: http://localhost:3000
echo   - 后端: http://localhost:8001
echo   - API 文档: http://localhost:8001/docs
echo   - 数据库: localhost:5432
echo.
echo 💡 提示:
echo   - 后端和前端在独立窗口中运行
echo   - 关闭窗口或按 Ctrl+C 停止服务
echo   - 停止数据库: docker-compose down
echo.
echo ======================================================================

pause

