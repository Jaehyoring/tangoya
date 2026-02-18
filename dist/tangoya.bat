@echo off
chcp 65001 >nul
:: tangoya.bat — Windows 실행 파일
:: 더블클릭하면 명령 프롬프트가 열리며 서버가 시작됩니다.

:: 이 파일이 있는 폴더로 이동
cd /d "%~dp0"

:: Python3 설치 여부 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [오류] Python이 설치되어 있지 않습니다.
    echo  https://www.python.org 에서 Python 3를 설치한 후 다시 실행해 주세요.
    echo  설치 시 "Add Python to PATH" 옵션을 반드시 체크해 주세요.
    echo.
    pause
    exit /b 1
)

echo ========================================
echo   tangoya (単語屋) 시작 중...
echo ========================================
python start_server.py
pause
