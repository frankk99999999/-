# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['launch.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('campus_trading.db', '.')],
    hiddenimports=['jinja2.ext', 'sqlalchemy.sql.default_comparator', 'jieba', 'sklearn', 'sklearn.feature_extraction.text', 'sklearn.metrics.pairwise', 'numpy'],
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
    [],
    exclude_binaries=True,
    name='校园二手交易平台',
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
    strip=False,
    upx=True,
    upx_exclude=[],
    name='校园二手交易平台',
)
