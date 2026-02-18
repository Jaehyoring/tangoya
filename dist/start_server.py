#!/usr/bin/env python3
"""
start_server.py — tangoya 로컬 서버 실행기
------------------------------------------
사용법:
  python3 dist/start_server.py

동작:
  1. 필요한 에셋(kuromoji.js, dict/, fonts/)이 없으면 자동으로 다운로드합니다
  2. dist/ 폴더를 루트로 HTTP 서버를 실행합니다 (포트 8000)
  3. 브라우저를 자동으로 열어 tangoya.html을 표시합니다
  4. Ctrl+C로 종료합니다

왜 서버가 필요한가:
  Kuromoji 형태소 분석기는 사전 파일(dict/*.dat.gz)을 XHR로 로드합니다.
  file:// 프로토콜에서는 보안 정책(CORS)으로 XHR이 차단되므로
  반드시 HTTP 서버를 통해 접근해야 합니다.
"""

import http.server
import webbrowser
import threading
import os
import sys
import socket
import time
import urllib.request
import urllib.error
import re

# ─────────────────────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────────────────────
# PyInstaller .app 번들로 실행될 때:
#   실행 파일 위치: tangoya.app/Contents/MacOS/tangoya
#   에셋 위치:      tangoya.app/../  (즉 .app 파일 옆)
# 일반 스크립트로 실행될 때:
#   __file__ 기준 폴더가 바로 에셋 폴더
def _find_asset_dir():
    if getattr(sys, 'frozen', False):
        # PyInstaller 번들: 실행파일의 3단계 위 (.app의 부모 폴더)
        exe_path = os.path.abspath(sys.executable)          # .app/Contents/MacOS/tangoya
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(exe_path))))
    return os.path.dirname(os.path.abspath(__file__))

DIST_DIR  = _find_asset_dir()
DICT_DIR  = os.path.join(DIST_DIR, 'dict')
FONTS_DIR = os.path.join(DIST_DIR, 'fonts')

PORT = 8000

# ─────────────────────────────────────────────────────────────
# 에셋 URL 설정
# ─────────────────────────────────────────────────────────────
KUROMOJI_VERSION   = '0.1.2'
KUROMOJI_JS_URL    = f'https://cdn.jsdelivr.net/npm/kuromoji@{KUROMOJI_VERSION}/build/kuromoji.js'
KUROMOJI_DICT_BASE = f'https://cdn.jsdelivr.net/npm/kuromoji@{KUROMOJI_VERSION}/dict'

DICT_FILES = [
    'base.dat.gz', 'cc.dat.gz', 'check.dat.gz',
    'tid.dat.gz', 'tid_map.dat.gz', 'tid_pos.dat.gz',
    'unk.dat.gz', 'unk_char.dat.gz', 'unk_compat.dat.gz',
    'unk_invoke.dat.gz', 'unk_map.dat.gz', 'unk_pos.dat.gz',
]

GOOGLE_FONTS_CSS_URL = (
    'https://fonts.googleapis.com/css2?'
    'family=Noto+Serif+JP:wght@400;700'
    '&family=Noto+Sans+KR:wght@300;400;500;700'
    '&family=DM+Mono:wght@400;500'
    '&display=swap'
)

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'


# ─────────────────────────────────────────────────────────────
# 에셋 존재 여부 확인
# ─────────────────────────────────────────────────────────────
def check_assets():
    """누락된 에셋 목록을 반환합니다."""
    missing = []

    # kuromoji.js
    if not os.path.exists(os.path.join(DIST_DIR, 'kuromoji.js')):
        missing.append('kuromoji.js')

    # dict 파일들
    missing_dict = [f for f in DICT_FILES
                    if not os.path.exists(os.path.join(DICT_DIR, f))]
    if missing_dict:
        missing.append(f'dict/ ({len(missing_dict)}개 파일 누락)')

    # fonts woff2
    woff2_files = []
    if os.path.isdir(FONTS_DIR):
        woff2_files = [f for f in os.listdir(FONTS_DIR) if f.endswith('.woff2')]
    if not woff2_files:
        missing.append('fonts/ (woff2 파일 없음)')

    return missing


# ─────────────────────────────────────────────────────────────
# 다운로드 유틸리티
# ─────────────────────────────────────────────────────────────
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def download_file(url, dest_path, label=None):
    label = label or os.path.basename(dest_path)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, \
             open(dest_path, 'wb') as f:
            downloaded = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
            size_kb = downloaded / 1024
            print(f'  ✓  {label:<42} {size_kb:>8.1f} KB')
    except urllib.error.URLError as e:
        print(f'  ✗  {label}: {e}', file=sys.stderr)
        raise


def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')


# ─────────────────────────────────────────────────────────────
# 에셋 다운로드 함수
# ─────────────────────────────────────────────────────────────
def _download_if_missing(url, dest, label=None):
    """파일이 없을 때만 다운로드합니다. 이미 존재하면 skip."""
    if os.path.exists(dest):
        return False
    download_file(url, dest, label or os.path.basename(dest))
    return True


def download_kuromoji_js():
    dest = os.path.join(DIST_DIR, 'kuromoji.js')
    if not _download_if_missing(KUROMOJI_JS_URL, dest, 'kuromoji.js'):
        print('  –  kuromoji.js 이미 존재 (skip)')


def download_dict_files():
    ensure_dir(DICT_DIR)
    missing = [f for f in DICT_FILES
               if not os.path.exists(os.path.join(DICT_DIR, f))]
    if not missing:
        print('  –  dict/ 파일 전부 존재 (skip)')
        return
    print(f'  Kuromoji 사전 파일 다운로드 중 ({len(missing)}개 누락, ~18 MB)...')
    for fname in missing:
        _download_if_missing(
            f'{KUROMOJI_DICT_BASE}/{fname}',
            os.path.join(DICT_DIR, fname),
            fname,
        )


def download_fonts():
    ensure_dir(FONTS_DIR)

    # 이미 woff2 파일이 있으면 스킵
    existing_woff2 = [f for f in os.listdir(FONTS_DIR) if f.endswith('.woff2')]
    if existing_woff2:
        print(f'  –  fonts/ woff2 파일 존재 ({len(existing_woff2)}개, skip)')
        return

    print('  Google Fonts CSS 가져오는 중...')
    css_text = fetch_text(GOOGLE_FONTS_CSS_URL)

    font_face_pattern = re.compile(r'@font-face\s*\{([^}]+)\}', re.DOTALL)
    url_pattern       = re.compile(r"url\(([^)]+\.woff2)\)")
    family_pattern    = re.compile(r"font-family:\s*'([^']+)'")
    style_pattern     = re.compile(r"font-style:\s*(\w+)")
    weight_pattern    = re.compile(r"font-weight:\s*(\w+)")
    unicode_pattern   = re.compile(r"unicode-range:\s*([^;]+);")

    new_font_faces  = []
    downloaded_urls = {}

    for m in font_face_pattern.finditer(css_text):
        block = m.group(1)
        url_m  = url_pattern.search(block)
        fam_m  = family_pattern.search(block)
        wgt_m  = weight_pattern.search(block)
        sty_m  = style_pattern.search(block)
        uni_m  = unicode_pattern.search(block)

        if not (url_m and fam_m):
            continue

        woff2_url     = url_m.group(1).strip().strip("'\"")
        family        = fam_m.group(1)
        weight        = wgt_m.group(1) if wgt_m else '400'
        style         = sty_m.group(1) if sty_m else 'normal'
        unicode_range = uni_m.group(1).strip() if uni_m else None

        if woff2_url not in downloaded_urls:
            url_hash    = woff2_url.split('/')[-1].replace('.woff2', '')
            safe_family = family.replace(' ', '')
            local_name  = f'{safe_family}-{weight}-{url_hash}.woff2'
            local_path  = os.path.join(FONTS_DIR, local_name)

            _download_if_missing(woff2_url, local_path, local_name)

            downloaded_urls[woff2_url] = local_name

        local_name = downloaded_urls[woff2_url]

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

    fonts_css_path    = os.path.join(FONTS_DIR, 'fonts.css')
    fonts_css_content = '\n\n'.join(new_font_faces) + '\n'
    with open(fonts_css_path, 'w', encoding='utf-8') as f:
        f.write(fonts_css_content)

    print(f'  ✓  fonts.css 생성 완료 ({len(new_font_faces)}개 @font-face, {len(downloaded_urls)}개 woff2)')


def run_setup():
    """누락된 에셋을 자동으로 다운로드합니다."""
    print()
    print('=' * 55)
    print('  tangoya — 초기 에셋 자동 다운로드')
    print('  (인터넷 연결이 필요합니다. 최초 1회만 실행됩니다)')
    print('=' * 55)

    print('\n[1/3] Kuromoji JS')
    download_kuromoji_js()

    print('\n[2/3] Kuromoji 사전 파일')
    download_dict_files()

    print('\n[3/3] Google Fonts (woff2)')
    download_fonts()

    print()
    print('=' * 55)
    print('  ✓ 에셋 준비 완료! 서버를 시작합니다...')
    print('=' * 55)
    print()


# ─────────────────────────────────────────────────────────────
# HTTP 서버
# ─────────────────────────────────────────────────────────────
def find_free_port(start_port):
    """사용 중인 포트를 피해 사용 가능한 포트를 반환합니다."""
    for port in range(start_port, start_port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port


# ─────────────────────────────────────────────────────────────
# 탭 닫힘 감지 — 워치독
# ─────────────────────────────────────────────────────────────
PING_TIMEOUT = 8  # 이 시간(초) 동안 ping 없으면 종료


class AppState:
    """서버 런타임 상태를 캡슐화합니다."""
    def __init__(self):
        self.last_ping  = time.time()  # 마지막 /ping 수신 시각
        self.app_opened = False        # 브라우저가 최초로 열렸는지 여부


_state = AppState()


def watchdog(server):
    """브라우저 탭이 닫혀 ping이 끊기면 서버를 종료합니다."""
    # 브라우저가 열릴 때까지 대기 (최대 30초)
    for _ in range(300):
        if _state.app_opened:
            break
        time.sleep(0.1)
    else:
        return  # 브라우저가 열리지 않은 경우 워치독 비활성화

    # 브라우저가 열린 후 ping 모니터링 시작
    # 처음 ping이 올 때까지 잠시 여유 부여
    time.sleep(PING_TIMEOUT + 2)

    while True:
        if time.time() - _state.last_ping > PING_TIMEOUT:
            print('\n  브라우저 탭이 닫혔습니다. 서버를 종료합니다.')
            server.server_close()
            os._exit(0)
        time.sleep(1)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """로그를 최소화한 HTTP 핸들러"""
    def log_message(self, format, *args):
        # 사전 파일 / 폰트 / ping 요청은 로그 생략
        path = args[0] if args else ''
        if '.dat.gz' in str(path) or '.woff2' in str(path) or '/ping' in str(path):
            return
        print(f'  [{self.address_string()}] {args[0]}')

    def do_GET(self):
        if self.path == '/ping':
            _state.last_ping  = time.time()
            _state.app_opened = True
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            super().do_GET()

    def end_headers(self):
        # dat.gz 파일에 CORS 헤더 추가
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────
def main():
    # dist/ 폴더를 서버 루트로 설정
    os.chdir(DIST_DIR)

    # 1. 누락 에셋 확인 → 자동 다운로드
    missing = check_assets()
    if missing:
        print()
        print('  ⚠️  다음 에셋이 없습니다:')
        for item in missing:
            print(f'      • {item}')
        run_setup()
    else:
        print()
        print('  ✓ 에셋 확인 완료 (모두 존재)')

    # 2. 다운로드 후 재확인
    still_missing = check_assets()
    if still_missing:
        print()
        print('  ✗ 에셋 다운로드에 실패했습니다:', file=sys.stderr)
        for item in still_missing:
            print(f'      • {item}', file=sys.stderr)
        print('  인터넷 연결을 확인 후 다시 실행해주세요.', file=sys.stderr)
        sys.exit(1)

    # 3. HTTP 서버 시작
    port = find_free_port(PORT)
    url  = f'http://localhost:{port}/tangoya.html'

    server = http.server.HTTPServer(('', port), QuietHandler)

    print('=' * 55)
    print('  tangoya 로컬 서버')
    print('=' * 55)
    print(f'  URL   : {url}')
    print(f'  루트  : {os.getcwd()}')
    print(f'  종료  : Ctrl + C')
    print('=' * 55)
    print()

    # 브라우저 자동 열기 (서버 시작 후 0.8초)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    # 탭 닫힘 감지 워치독 스레드
    wd = threading.Thread(target=watchdog, args=(server,), daemon=True)
    wd.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  서버를 종료합니다.')
        server.server_close()


if __name__ == '__main__':
    main()
