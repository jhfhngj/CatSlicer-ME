# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['frontend.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\ezzel\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\flet_video', 'flet_video'),],
    hiddenimports=['flet_video'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='frontend',
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
    version='C:\\Users\\ezzel\\AppData\\Local\\Temp\\cde02bd7-0266-4aee-a8ae-175442e064fc',
)
