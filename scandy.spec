from PyInstaller.building.api import *
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import sys
import os

block_cipher = None

# Server Analysis
server = Analysis(
    ['run.py'],  # Hauptdatei für den Server
    pathex=[],
    binaries=[],
    datas=[
        ('app/templates', 'app/templates'),
        ('app/static', 'app/static'),
        ('instance', 'instance'),
        ('.env', '.'),
        ('app/database', 'app/database'),
    ],
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'werkzeug.security',
        'flask_migrate',
        'flask_session',
        'sqlalchemy',
        'jinja2.ext',
        'flask_compress',
        'flask_cors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Client Analysis
client = Analysis(
    ['run_client.py'],  # Hauptdatei für den Client
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'requests',
        'json',
        'sys',
        'os',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Server PYZ
server_pyz = PYZ(server.pure, server.zipped_data, cipher=block_cipher)

# Client PYZ
client_pyz = PYZ(client.pure, client.zipped_data, cipher=block_cipher)

# Server EXE
server_exe = EXE(
    server_pyz,
    server.scripts,
    [],
    exclude_binaries=True,
    name='scandy_server',
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

# Client EXE
client_exe = EXE(
    client_pyz,
    client.scripts,
    [],
    exclude_binaries=True,
    name='scandy_client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # False für GUI-Anwendung
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Server COLLECT
server_collect = COLLECT(
    server_exe,
    server.binaries,
    server.zipfiles,
    server.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='server',
)

# Client COLLECT
client_collect = COLLECT(
    client_exe,
    client.binaries,
    client.zipfiles,
    client.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='client',
) 