# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['qt_main.py'],
    pathex=[],
    binaries=[],
    datas=[('fonts', 'fonts'), ('templates', 'templates'), ('reports', 'reports')],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'sqlite3', 'json', 'os', 'sys', 'pathlib', 'jdatetime', 'shutil', 'datetime', 'time'],
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
    name='RadiologySystem',
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
    icon=['logo.png'],
)
