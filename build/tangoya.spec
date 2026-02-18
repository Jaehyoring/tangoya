# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — tangoya macOS .app 번들

import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
DIST_DIR = os.path.join(ROOT, 'dist')

a = Analysis(
    [os.path.join(DIST_DIR, 'start_server.py')],
    pathex=[DIST_DIR],
    binaries=[],
    datas=[],          # 에셋은 런타임에 .app 옆 폴더에서 읽음
    hiddenimports=[
        'http.server',
        'urllib.request',
        'urllib.error',
        'webbrowser',
        'threading',
        'socket',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tangoya',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # 터미널 창 없음
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='tangoya.app',
    icon=None,
    bundle_identifier='com.jaehyoring.tangoya',
    info_plist={
        'CFBundleName': 'tangoya',
        'CFBundleDisplayName': 'tangoya',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    },
)
