@echo off
chcp 65001 > nul
rem ─────────────────────────────────────────────────────
rem  tangoya (単語屋) — Windows 실행기
rem  더블클릭으로 실행하세요.
rem ─────────────────────────────────────────────────────

rem 이 배치 파일이 있는 폴더로 이동
cd /d "%~dp0"

echo ================================================
echo   tangoya (単語屋) 시작 중...
echo ================================================
echo.

rem Python3 존재 여부 확인
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo        https://www.python.org 에서 Python 3.6 이상을 설치해주세요.
    echo.
    pause
    exit /b 1
)

rem Python 버전 확인 (3.x 인지)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python %PYVER% 감지됨
echo.

python dist\start_server.py

rem 오류 발생 시 창 유지
if %errorlevel% neq 0 (
    echo.
    echo [오류] 실행에 실패했습니다. (종료 코드: %errorlevel%)
    pause
)
