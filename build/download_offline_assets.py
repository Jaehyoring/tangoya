#!/usr/bin/env python3
"""
download_offline_assets.py
--------------------------
tangoya 오프라인 동작에 필요한 로컬 에셋을 준비합니다.

실행 조건:
  - 인터넷 연결 필요 (최초 1회)
  - Python 3.6+

실행 방법:
  cd <프로젝트 루트>
  python3 build/download_offline_assets.py

결과:
  dist/kuromoji.js       — Kuromoji v0.1.2 브라우저 빌드
  dist/dict/*.dat.gz     — Kuromoji 사전 파일 12개 (~17.8 MB)
  dist/fonts/*.woff2     — Noto Serif JP / Noto Sans KR / DM Mono
  dist/fonts/fonts.css   — @font-face 정의
"""

import os
import sys
import shutil
import urllib.request
import urllib.error
import re

# ─────────────────────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DIST_DIR    = os.path.join(PROJECT_DIR, 'dist')
DICT_DIR    = os.path.join(DIST_DIR, 'dict')
FONTS_DIR   = os.path.join(DIST_DIR, 'fonts')

KUROMOJI_VERSION = '0.1.2'
KUROMOJI_JS_URL  = f'https://cdn.jsdelivr.net/npm/kuromoji@{KUROMOJI_VERSION}/build/kuromoji.js'
KUROMOJI_DICT_BASE = f'https://cdn.jsdelivr.net/npm/kuromoji@{KUROMOJI_VERSION}/dict'

DICT_FILES = [
    'base.dat.gz',
    'cc.dat.gz',
    'check.dat.gz',
    'tid.dat.gz',
    'tid_map.dat.gz',
    'tid_pos.dat.gz',
    'unk.dat.gz',
    'unk_char.dat.gz',
    'unk_compat.dat.gz',
    'unk_invoke.dat.gz',
    'unk_map.dat.gz',
    'unk_pos.dat.gz',
]

# Google Fonts CSS URL (모든 weight 포함)
GOOGLE_FONTS_CSS_URL = (
    'https://fonts.googleapis.com/css2?'
    'family=Noto+Serif+JP:wght@400;700'
    '&family=Noto+Sans+KR:wght@300;400;500;700'
    '&family=DM+Mono:wght@400;500'
    '&display=swap'
)

# User-Agent: 최신 Chrome (Google Fonts API 응답에 woff2 포함하도록)
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'


# ─────────────────────────────────────────────────────────────
# 유틸리티
# ─────────────────────────────────────────────────────────────
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def download(url, dest_path, label=None):
    label = label or os.path.basename(dest_path)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, \
             open(dest_path, 'wb') as f:
            total = int(resp.headers.get('Content-Length', 0))
            downloaded = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
            size_kb = downloaded / 1024
            print(f'  ✓  {label:<40} {size_kb:>8.1f} KB')
    except urllib.error.URLError as e:
        print(f'  ✗  {label}: {e}', file=sys.stderr)
        raise


def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


# ─────────────────────────────────────────────────────────────
# Step 1: kuromoji.js
# ─────────────────────────────────────────────────────────────
def download_kuromoji_js():
    dest = os.path.join(DIST_DIR, 'kuromoji.js')
    if os.path.exists(dest):
        print(f'  –  kuromoji.js 이미 존재 (skip)')
        return
    print(f'  Kuromoji JS 다운로드 중...')
    download(KUROMOJI_JS_URL, dest, 'kuromoji.js')


# ─────────────────────────────────────────────────────────────
# Step 2: Kuromoji 사전 파일
# ─────────────────────────────────────────────────────────────
def download_dict_files():
    ensure_dir(DICT_DIR)
    print(f'  Kuromoji 사전 파일 다운로드 중 (총 {len(DICT_FILES)}개, ~18 MB)...')
    for fname in DICT_FILES:
        dest = os.path.join(DICT_DIR, fname)
        if os.path.exists(dest):
            print(f'  –  {fname:<40} (skip)')
            continue
        url = f'{KUROMOJI_DICT_BASE}/{fname}'
        download(url, dest, fname)


# ─────────────────────────────────────────────────────────────
# Step 3: Google Fonts → woff2 + fonts.css
# ─────────────────────────────────────────────────────────────
def download_fonts():
    ensure_dir(FONTS_DIR)
    print('  Google Fonts CSS 가져오는 중...')
    css_text = fetch_text(GOOGLE_FONTS_CSS_URL)

    # CSS 안의 woff2 URL 파싱
    # 패턴: url(https://fonts.gstatic.com/...woff2)  and  font-family: '...'
    # @font-face 블록 단위로 파싱
    font_face_pattern = re.compile(
        r'@font-face\s*\{([^}]+)\}', re.DOTALL
    )
    url_pattern     = re.compile(r"url\(([^)]+\.woff2)\)")
    family_pattern  = re.compile(r"font-family:\s*'([^']+)'")
    style_pattern   = re.compile(r"font-style:\s*(\w+)")
    weight_pattern  = re.compile(r"font-weight:\s*(\w+)")
    unicode_pattern = re.compile(r"unicode-range:\s*([^;]+);")

    new_font_faces = []
    downloaded_urls = {}  # url → local filename

    for m in font_face_pattern.finditer(css_text):
        block = m.group(1)
        url_m    = url_pattern.search(block)
        fam_m    = family_pattern.search(block)
        wgt_m    = weight_pattern.search(block)
        sty_m    = style_pattern.search(block)
        uni_m    = unicode_pattern.search(block)

        if not (url_m and fam_m):
            continue

        woff2_url = url_m.group(1).strip().strip("'\"")
        family    = fam_m.group(1)
        weight    = wgt_m.group(1) if wgt_m else '400'
        style     = sty_m.group(1) if sty_m else 'normal'
        unicode_range = uni_m.group(1).strip() if uni_m else None

        # 로컬 파일명 결정 (family + weight + 해시 일부)
        if woff2_url not in downloaded_urls:
            # URL 끝 부분에서 고유 식별자 추출
            url_hash = woff2_url.split('/')[-1].replace('.woff2', '')
            safe_family = family.replace(' ', '')
            local_name  = f'{safe_family}-{weight}-{url_hash}.woff2'
            local_path  = os.path.join(FONTS_DIR, local_name)

            if not os.path.exists(local_path):
                download(woff2_url, local_path, local_name)
            else:
                print(f'  –  {local_name} (skip)')

            downloaded_urls[woff2_url] = local_name

        local_name = downloaded_urls[woff2_url]

        # 새 @font-face 블록 생성
        face_lines = [
            '@font-face {',
            f"  font-family: '{family}';",
            f'  font-style: {style};',
            f'  font-weight: {weight};',
            f"  src: url('{local_name}') format('woff2');",
        ]
        if unicode_range:
            face_lines.append(f'  unicode-range: {unicode_range};')
        face_lines.append('}')
        new_font_faces.append('\n'.join(face_lines))

    # fonts.css 저장
    fonts_css_path = os.path.join(FONTS_DIR, 'fonts.css')
    fonts_css_content = '\n\n'.join(new_font_faces) + '\n'
    with open(fonts_css_path, 'w', encoding='utf-8') as f:
        f.write(fonts_css_content)

    face_count = len(new_font_faces)
    file_count = len(downloaded_urls)
    print(f'  ✓  fonts.css 생성 완료 ({face_count}개 @font-face, {file_count}개 woff2 파일)')


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────
def main():
    print('=' * 60)
    print('tangoya 오프라인 에셋 준비')
    print('=' * 60)

    ensure_dir(DIST_DIR)

    print('\n[1/3] Kuromoji JS')
    download_kuromoji_js()

    print('\n[2/3] Kuromoji 사전 파일')
    download_dict_files()

    print('\n[3/3] Google Fonts (woff2)')
    download_fonts()

    print('\n' + '=' * 60)
    print('완료!')
    print(f'  dist/kuromoji.js')
    print(f'  dist/dict/     ({len(DICT_FILES)}개 파일)')
    print(f'  dist/fonts/    (woff2 + fonts.css)')
    print()
    print('다음 단계:')
    print('  python3 dist/start_server.py  →  브라우저 자동 실행')
    print('=' * 60)


if __name__ == '__main__':
    main()
