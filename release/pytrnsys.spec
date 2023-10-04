# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = []
datas += collect_data_files("pytrnsys")
datas += collect_data_files("trnsysGUI")

block_cipher = None

a = Analysis(
    ["run_pytrnsys.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["pytrnsys", *collect_submodules("pytrnsys")],
    hookspath=[],
    hooksconfig={"matplotlib": {"backends": ["AGG", "PDF"]}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="pytrnsys",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    hide_console="hide-early",
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

ga = Analysis(
    ["run_pytrnsys_gui.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={"matplotlib": {"backends": ["AGG", "PDF"]}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

gpyz = PYZ(ga.pure)

gexe = EXE(
    gpyz,
    ga.scripts,
    [],
    name="pytrnsys-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    gexe,
    ga.binaries,
    ga.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pytrnsys",
)
