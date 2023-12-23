# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['todo_main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    name='CheXy',
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
    icon=['/Users/nathanm/Downloads/to_do-main/CheXy.png'],
)
app = BUNDLE(
    exe,
    name='CheXy.app',
    icon='/Users/nathanm/Downloads/to_do-main/CheXy.png',
    bundle_identifier=None,
)
