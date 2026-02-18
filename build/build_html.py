#!/usr/bin/env python3
"""
build_html.py  —  tangoya 빌드 자동화 스크립트
실행: cd tangoya && python3 build/build_html.py

처리 흐름:
  1. data/N1~N5_words_naver.txt 읽기
  2. data/korean_dict.json 로드
  3. JLPT_DICT 생성 (한자키 + 히라가나키, r/l/k 포함)
  4. dist/tangoya_template.html 읽기
  5. // __JLPT_DICT_PLACEHOLDER__ → const JLPT_DICT = {...};
  6. dist/tangoya.html 저장
  7. 완료 통계 출력
"""

import json
import os
import sys
from datetime import datetime

# ── 경로 설정 ──────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.dirname(SCRIPT_DIR)          # tangoya/
DATA_DIR   = os.path.join(BASE_DIR, "data")
DIST_DIR   = os.path.join(BASE_DIR, "dist")

WORD_FILES = [
    ("N5", os.path.join(DATA_DIR, "N5_words_naver.txt")),
    ("N4", os.path.join(DATA_DIR, "N4_words_naver.txt")),
    ("N3", os.path.join(DATA_DIR, "N3_words_naver.txt")),
    ("N2", os.path.join(DATA_DIR, "N2_words_naver.txt")),
    ("N1", os.path.join(DATA_DIR, "N1_words_naver.txt")),
]
KOREAN_PATH  = os.path.join(DATA_DIR, "korean_dict.json")
TEMPLATE_PATH = os.path.join(DIST_DIR, "tangoya_template.html")
OUTPUT_PATH   = os.path.join(DIST_DIR, "tangoya.html")
PLACEHOLDER   = "  // __JLPT_DICT_PLACEHOLDER__"


def main():
    print("=" * 56)
    print("  tangoya build_html.py")
    print("=" * 56)

    # ── STEP 1: N1~N5 단어 파일 읽기 ─────────────────────
    print("\n[1/4] 단어 파일 로드 중...")
    word_data = []   # [(level, reading, kanji), ...]
    for level, fpath in WORD_FILES:
        if not os.path.exists(fpath):
            print(f"  [WARNING] 파일 없음: {fpath}")
            continue
        count = 0
        with open(fpath, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) < 3:
                    continue
                reading = parts[0].strip()
                kanji   = parts[1].strip()
                word_data.append((level, reading, kanji))
                count += 1
        print(f"  {level}: {count}줄 읽음")

    # ── STEP 2: korean_dict.json 로드 ─────────────────────
    print("\n[2/4] korean_dict.json 로드 중...")
    if os.path.exists(KOREAN_PATH):
        with open(KOREAN_PATH, "r", encoding="utf-8") as f:
            korean_dict = json.load(f)
        print(f"  로드 완료: {len(korean_dict):,}개 항목")
    else:
        korean_dict = {}
        print("  [WARNING] korean_dict.json 없음 — 한국어 뜻 없이 진행")

    # ── STEP 3: JLPT_DICT 생성 ────────────────────────────
    print("\n[3/4] JLPT_DICT 생성 중...")
    jlpt_dict   = {}
    level_count = {lvl: 0 for lvl, _ in WORD_FILES}

    for level, reading, kanji in word_data:
        korean = (
            korean_dict.get(kanji)
            or korean_dict.get(reading)
            or "-"
        )
        entry = {"r": reading, "l": level, "k": korean}

        # 한자표기 키 등록 (N5 우선 — 먼저 등록된 항목 유지)
        if kanji and kanji not in jlpt_dict:
            jlpt_dict[kanji] = entry
            level_count[level] += 1

        # 히라가나 키 등록 (한자키와 다를 때만)
        if reading != kanji and reading not in jlpt_dict:
            jlpt_dict[reading] = entry

    total      = len(jlpt_dict)
    has_korean = sum(1 for v in jlpt_dict.values()
                     if v["k"] != "-" and v["k"])
    missing    = total - has_korean

    print(f"  전체 항목: {total:,}개")
    print(f"  레벨별 (한자키 기준):")
    for lvl, _ in WORD_FILES:
        print(f"    {lvl}: {level_count[lvl]:>5}개")

    # JSON 직렬화 (minified)
    dict_json = json.dumps(jlpt_dict, ensure_ascii=False, separators=(",", ":"))

    # ── STEP 4~6: 템플릿 → HTML 출력 ─────────────────────
    print("\n[4/4] HTML 빌드 중...")
    if not os.path.exists(TEMPLATE_PATH):
        print(f"  [ERROR] 템플릿 없음: {TEMPLATE_PATH}")
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    if PLACEHOLDER not in template:
        print(f"  [ERROR] 플레이스홀더 '{PLACEHOLDER}' 를 템플릿에서 찾을 수 없습니다.")
        sys.exit(1)

    # 플레이스홀더 → const JLPT_DICT = {...};
    replacement = f"  const JLPT_DICT = {dict_json};"
    output_html = template.replace(PLACEHOLDER, replacement, 1)

    os.makedirs(DIST_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output_html)

    file_kb = os.path.getsize(OUTPUT_PATH) / 1024

    # ── 완료 통계 출력 ────────────────────────────────────
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("=" * 56)
    print("  빌드 완료")
    print("=" * 56)
    print(f"  단어 데이터: {total:,}개 항목 내장 (한국어 뜻 포함: {has_korean:,}개)")
    print(f"  출력 파일  : {OUTPUT_PATH}")
    print(f"  파일 크기  : {file_kb:.1f} KB")
    print(f"  빌드 완료  : {now}")
    print("=" * 56)


if __name__ == "__main__":
    main()
