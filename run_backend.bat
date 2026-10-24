@echo off
chcp 65001 >nul
cd /d %~dp0backend
echo ============================================
echo   He thong Quan ly CLB Sinh vien + AI
echo ============================================
echo.

set PY=.venv\Scripts\python.exe

REM --- Tu tao venv bang uv neu chua co ---
if not exist "%PY%" (
    echo [1/4] Tao moi truong ao .venv...
    where uv >nul 2>nul && (uv venv) || (python -m venv .venv)
)

echo [2/4] Cai dat dependencies...
"%PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    where uv >nul 2>nul && (uv pip install --python "%PY%" -r requirements.txt) || ("%PY%" -m ensurepip && "%PY%" -m pip install -r requirements.txt)
) else (
    "%PY%" -m pip install -r requirements.txt
)
if errorlevel 1 goto :error

if not exist club_management.db (
    echo [3/4] Tao du lieu mau...
    "%PY%" seed.py
) else (
    echo [3/4] Database da ton tai - bo qua seed.
)

echo [4/4] Khoi dong server FastAPI...
echo.
echo   Web app : http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Tai khoan: chunhiem / 123456
echo.
"%PY%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto :done

:error
echo.
echo [LOI] Co loi xay ra. Kiem tra Python da cai dat chua.
pause
:done
pause