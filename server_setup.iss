#define MyAppName "Scandy Server"
#define MyAppVersion "1.0"
#define MyAppPublisher "BTZ"
#define MyAppURL "https://www.btz.de/"
#define MyAppExeName "scandy_server.exe"

[Setup]
AppId={{B1C2D3E4-F5G6-H7I8-J9K0-L1M2N3O4P5Q6}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\ScandyServer
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=scandy_server_setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CreateAppDir=yes
SetupLogging=yes
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon=none

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Dirs]
Name: "{app}"

[Files]
Source: "dist\scandy_server\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} Console"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--console"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Server starten"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}" 