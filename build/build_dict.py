#!/usr/bin/env python3
"""
build_dict.py
N1~N5 단어 파일 5개 + korean_dict.json → jlpt_dict.json 생성
"""

import json
import os

# ── 경로 설정 ──────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
BUILD_DIR  = os.path.join(BASE_DIR, "build")
OUT_PATH   = os.path.join(BUILD_DIR, "jlpt_dict.json")

WORD_FILES = [
    ("N5", os.path.join(DATA_DIR, "N5_words_naver.txt")),
    ("N4", os.path.join(DATA_DIR, "N4_words_naver.txt")),
    ("N3", os.path.join(DATA_DIR, "N3_words_naver.txt")),
    ("N2", os.path.join(DATA_DIR, "N2_words_naver.txt")),
    ("N1", os.path.join(DATA_DIR, "N1_words_naver.txt")),
]
KOREAN_PATH = os.path.join(DATA_DIR, "korean_dict.json")


# ── korean_dict.json 로드 ──────────────────────────────────
if os.path.exists(KOREAN_PATH):
    with open(KOREAN_PATH, "r", encoding="utf-8") as f:
        korean_dict = json.load(f)
    print(f"[INFO] korean_dict.json 로드 완료: {len(korean_dict)}개")
else:
    korean_dict = {}
    print("[WARNING] korean_dict.json 없음 - 한국어 뜻 없이 진행합니다.")


# ── 메인 사전 구축 ─────────────────────────────────────────
jlpt_dict   = {}          # 최종 출력 사전
level_count = {lvl: 0 for lvl, _ in WORD_FILES}   # 레벨별 신규 등록 수

for level, fpath in WORD_FILES:
    if not os.path.exists(fpath):
        print(f"[WARNING] 파일 없음: {fpath}")
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue

        parts = line.split(",")
        if len(parts) < 3:
            print(f"[SKIP] {fpath} 줄 {lineno}: 컬럼 부족 → {repr(line)}")
            continue

        reading = parts[0].strip()   # 히라가나
        kanji   = parts[1].strip()   # 한자표기 (없으면 히라가나와 동일할 수 있음)
        # level은 파일명에서 확정 (parts[2]는 참고용)

        # 한국어 뜻 조회: 한자표기 우선, 없으면 히라가나 키로 재시도
        korean = (
            korean_dict.get(kanji)
            or korean_dict.get(reading)
            or "-"
        )

        entry = {"r": reading, "l": level, "k": korean}

        # ── 한자표기 키 등록 (충돌 시 먼저 등록된 항목 유지) ──
        if kanji and kanji not in jlpt_dict:
            jlpt_dict[kanji] = entry
            level_count[level] += 1

        # ── 히라가나 키 등록 (한자표기와 다를 때만, 충돌 시 유지) ──
        if reading != kanji and reading not in jlpt_dict:
            jlpt_dict[reading] = entry


# ── 출력 ───────────────────────────────────────────────────
os.makedirs(BUILD_DIR, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(jlpt_dict, f, ensure_ascii=False, separators=(",", ":"))

file_kb = os.path.getsize(OUT_PATH) / 1024


# ── 통계 출력 ──────────────────────────────────────────────
has_korean = sum(1 for v in jlpt_dict.values()
                 if v["k"] != "-" and v["k"])
missing    = sum(1 for v in jlpt_dict.values() if v["k"] == "-")

print()
print("=" * 50)
print("  jlpt_dict.json 생성 완료")
print("=" * 50)
print(f"  저장 경로  : {OUT_PATH}")
print(f"  파일 크기  : {file_kb:.1f} KB")
print()
print("  레벨별 신규 등록 항목 수 (한자표기 키 기준)")
for lvl, _ in WORD_FILES:
    print(f"    {lvl}: {level_count[lvl]:>5}개")
print()
print(f"  전체 항목 수    : {len(jlpt_dict):>6}개")
print(f"  한국어 뜻 포함  : {has_korean:>6}개")
print(f"  한국어 뜻 누락  : {missing:>6}개")
print()
print("  샘플 5개:")

samples = [
    ("会う",   "あう"),
    ("食べる",  "たべる"),
    ("学校",   "がっこう"),
    ("電車",   "でんしゃ"),
    ("勉強",   "べんきょう"),
]
for kanji_key, reading_key in samples:
    # 한자키 우선, 없으면 히라가나 키로
    entry = jlpt_dict.get(kanji_key) or jlpt_dict.get(reading_key)
    if entry:
        print(f"    {kanji_key:<10} → r:{entry['r']}, l:{entry['l']}, k:{entry['k']}")
    else:
        print(f"    {kanji_key:<10} → (사전 없음)")

print("=" * 50)
