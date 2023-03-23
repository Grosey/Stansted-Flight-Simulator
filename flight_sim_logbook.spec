# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['flight_sim_logbook.pyw'],
    pathex=[],
    binaries=[],
    datas=[
        ('stansted-flight-simulator-log-firebase-adminsdk-jxh61-4fb61497f6.json', '.'),
        ('certificate blank.jpg', '.'),
        ('arial.ttf', '.')
    ],
    hiddenimports=['babel.numbers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='flight_sim_logbook',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['thumbnail_cf23fcb6.ico'],
)
