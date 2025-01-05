#define MyAppName "Scandy Client"
#define MyAppVersion "1.0"
#define MyAppPublisher "BTZ"
#define MyAppURL "https://www.btz.de/"
#define MyAppExeName "scandy_client.exe"

[Setup]
AppId={{C1D2E3F4-G5H6-I7J8-K9L0-M1N2O3P4Q5R6}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\ScandyClient
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=scandy_client_setup
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

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{app}"

[Files]
Source: "dist\scandy_client\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}" 