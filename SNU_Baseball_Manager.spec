# -*- mode: python ; coding: utf-8 -*-
"""
macOS .app 빌드용 PyInstaller 스펙 파일
사용법:
    pyinstaller SNU_Baseball_Manager.spec
결과물: dist/SNU Baseball Manager.app

아이콘 추가:
    icon.icns 파일을 이 폴더에 넣고 아래 icon= 줄 주석 해제
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/players.xlsx',   'data'),
        ('data/cpu_teams.xlsx', 'data'),
    ],
    hiddenimports=[
        'openpyxl',
        'openpyxl.cell._writer',
        'pygame',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SNU Baseball Manager',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    # icon='icon.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SNU Baseball Manager',
)

app = BUNDLE(
    coll,
    name='SNU Baseball Manager.app',
    # icon='icon.icns',
    bundle_identifier='com.snubaseball.manager',
    info_plist={
        'CFBundleName': 'SNU Baseball Manager',
        'CFBundleDisplayName': 'SNU Baseball Manager',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
)
