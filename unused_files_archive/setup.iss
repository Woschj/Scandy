#define MyAppName "Scandy"
#define MyAppVersion "1.0"
#define MyAppPublisher "BTZ"
#define MyAppURL "https://www.btz.de/"
#define MyAppExeName "scandy_client.exe"
#define MyAppServerExeName "scandy_server.exe"

[Setup]
AppId={{D1E2F3G4-H5I6-J7K8-L9M0-N1O2P3Q4R5S6}}
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

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\scandy_server\*"; DestDir: "{app}\server"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\scandy_client\*"; DestDir: "{app}\client"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName} Server"; Filename: "{app}\server\{#MyAppServerExeName}"
Name: "{group}\{#MyAppName} Client"; Filename: "{app}\client\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\client\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\server\{#MyAppServerExeName}"; Description: "Server starten"; Flags: nowait postinstall skipifsilent shellexec
Filename: "{app}\client\{#MyAppExeName}"; Description: "Client starten"; Flags: nowait postinstall skipifsilent unchecked shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}" 