#define MyAppName "Scandy"
#define MyAppVersion "1.0"
#define MyAppPublisher "BTZ"
#define MyAppURL "https://www.btz.de/"
#define MyAppExeName "scandy_client.exe"
#define MyAppServerExeName "scandy_server.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-G7H8-I9J0-K1L2M3N4O5P6}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=scandy_setup
Compression=lzma
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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}\server"
Name: "{app}\client"

[Files]
Source: "dist\server\*"; DestDir: "{app}\server"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\client\*"; DestDir: "{app}\client"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName} Client"; Filename: "{app}\client\{#MyAppExeName}"
Name: "{group}\{#MyAppName} Server"; Filename: "{app}\server\{#MyAppServerExeName}"
Name: "{group}\{#MyAppName} Server Console"; Filename: "{app}\server\{#MyAppServerExeName}"; Parameters: "--console"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\client\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\server\{#MyAppServerExeName}"; Description: "Server starten"; Flags: nowait postinstall skipifsilent shellexec
Filename: "{app}\client\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}" 