#!/bin/bash
# ─────────────────────────────────────────────────────
#  tangoya (単語屋) — macOS 실행기
#  더블클릭으로 실행하세요.
# ─────────────────────────────────────────────────────

# 이 스크립트가 있는 폴더로 이동 (어디서 실행해도 OK)
cd "$(dirname "$0")"

# Python3 존재 여부 확인
if ! command -v python3 &>/dev/null; then
  osascript -e 'display alert "Python3가 필요합니다" message "https://www.python.org 에서 Python 3.6 이상을 설치해주세요." as critical'
  exit 1
fi

echo "================================================"
echo "  tangoya (単語屋) 시작 중..."
echo "================================================"
echo ""

python3 dist/start_server.py
