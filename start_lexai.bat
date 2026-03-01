@echo off
title LexAI - Starting All Services
color 0A

echo ============================================
echo   LexAI - AI Copilot untuk Praktisi Hukum
echo ============================================
echo.
echo Starting all services...
echo.

:: Start AI Service (Python FastAPI)
echo [1/3] Starting AI Service (port 8000)...
start "LexAI - AI Service" cmd /k "cd /d d:\lexAI\ai-service && python main.py"
timeout /t 3 /nobreak > nul

:: Start Backend (Node.js Express)
echo [2/3] Starting Backend (port 3001)...
start "LexAI - Backend" cmd /k "cd /d d:\lexAI\backend && npm run dev"
timeout /t 2 /nobreak > nul

:: Start Frontend (Next.js)
echo [3/3] Starting Frontend (port 3000)...
start "LexAI - Frontend" cmd /k "cd /d d:\lexAI\frontend && npm run dev"
timeout /t 3 /nobreak > nul

echo.
echo ============================================
echo   Semua service berhasil dijalankan!
echo ============================================
echo.
echo   Frontend  : http://localhost:3000
echo   Backend   : http://localhost:3001
echo   AI Service: http://localhost:8000
echo.
echo   Buka http://localhost:3000 di browser
echo.
echo   Untuk stop: tutup semua window CMD
echo ============================================
echo.
pause
