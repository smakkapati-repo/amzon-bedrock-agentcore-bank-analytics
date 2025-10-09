@echo off
echo Starting BankIQ+ on Windows...
echo.

echo [1/2] Starting Backend Server (Flask)...
start "Backend Server" cmd /k "cd backend && python app.py"

echo [2/2] Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak > nul

echo [2/2] Starting Frontend Server (React)...
start "Frontend Server" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo BankIQ+ is starting up!
echo ========================================
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:3000
echo.
echo Wait for both servers to fully start,
echo then open: http://localhost:3000
echo.
echo Press any key to exit this window...
pause > nul