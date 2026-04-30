# -*- mode: python ; coding: utf-8 -*-
# Windows .exe 빌드 전용

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
    # icon='icon.ico',
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
