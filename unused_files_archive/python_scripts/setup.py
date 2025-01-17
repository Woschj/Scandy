from cx_Freeze import setup, Executable
import sys
import os

# Basis-Verzeichnis für relative Pfade
base_dir = os.path.abspath(os.path.dirname(__file__))

# Abhängigkeiten aus requirements.txt lesen
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Gemeinsame Build-Optionen
build_options = {
    'packages': [],
    'excludes': [],
    'include_files': [
        ('app', 'app'),
        ('instance', 'instance'),
        ('.env', '.env'),
        ('requirements.txt', 'requirements.txt')
    ]
}

# Server-Executable
server_exe = Executable(
    script='run.py',
    target_name='scandy_server.exe',
    base='console'
)

# Client-Executable
client_exe = Executable(
    script='run_client.py',
    target_name='scandy_client.exe',
    base='Win32GUI' if sys.platform == 'win32' else None
)

setup(
    name='Scandy',
    version='1.0',
    description='Scandy Application',
    options={'build_exe': build_options},
    executables=[server_exe, client_exe],
    install_requires=requirements
) 