# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


capture = Analysis(
    ['statsanalyzer/capture.py'],
    pathex=['statsanalyzer'],
    binaries=[],
    datas=[],
    hiddenimports=['pg8000', 'fsspec', 's3fs', 'fsspec'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

report = Analysis(
    ['statsanalyzer/report.py'],
    pathex=['statsanalyzer'],
    binaries=[],
    datas=[],
    hiddenimports=['fsspec', 's3fs'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_capture = PYZ(capture.pure, capture.zipped_data, cipher=block_cipher)

exe_capture = EXE(
    pyz_capture,
    capture.scripts,
    [],
    exclude_binaries=True,
    name='capture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

pyz_report = PYZ(report.pure, report.zipped_data, cipher=block_cipher)

exe_report = EXE(
    pyz_report,
    report.scripts,
    [],
    exclude_binaries=True,
    name='report',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe_capture,
    capture.binaries,
    capture.zipfiles,
    capture.datas,
    exe_report,
    report.binaries,
    report.zipfiles,
    report.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='statsanalyzer',
)
