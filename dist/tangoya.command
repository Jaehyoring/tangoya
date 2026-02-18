#!/bin/bash
# tangoya.command — macOS 실행 파일
# Finder에서 더블클릭하면 터미널이 열리며 서버가 시작됩니다.

# 이 파일이 있는 폴더로 이동
cd "$(dirname "$0")"

# Python3 설치 여부 확인
if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python3가 설치되어 있지 않습니다." message "https://www.python.org 에서 Python 3를 설치한 후 다시 실행해 주세요." as critical'
    exit 1
fi

echo "========================================"
echo "  tangoya (単語屋) 시작 중..."
echo "========================================"
python3 start_server.py
