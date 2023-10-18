# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


block_cipher = None

a = Analysis(
    ["runPytrnsys.py"],
    pathex=[],
    binaries=[],
    datas=collect_data_files("pytrnsys"),
    hiddenimports=collect_submodules("pytrnsys"),
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
    exclude_binaries=True,
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
    ["runPytrnsysGui.py"],
    pathex=[],
    binaries=[],
    datas=[*collect_data_files("trnsysGUI"), *copy_metadata("jupyter_client")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
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
    exclude_binaries=True,
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

ka = Analysis(
    ["launchIPythonKernel.py"],
    pathex=[],
    binaries=[],
    datas=collect_data_files("pytrnsys"),
    hiddenimports=["ipykernel.kernelapp", *collect_submodules("pytrnsys")],
    hookspath=[],
    hooksconfig={"matplotlib": {"backends": ["AGG", "PDF"]}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

kpyz = PYZ(ka.pure)

kexe = EXE(
    kpyz,
    ka.scripts,
    [],
    exclude_binaries=True,
    name="launchIPythonKernel",
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
    kexe,
    ka.binaries,
    ka.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pytrnsys",
)
