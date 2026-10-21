; Build with Inno Setup 6 on Windows after PyInstaller. No database/data deletion.
#ifndef AppVersion
#define AppVersion "0.14.0-research"
#endif
[Setup]
AppId={{14F0FE68-3708-49D3-BA5F-054CBF5146C1}
AppName=StarGate Research
AppVersion={#AppVersion}
VersionInfoVersion=0.14.0.0
DefaultDirName={localappdata}\Programs\StarGate
DefaultGroupName=StarGate Research
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\installer
OutputBaseFilename=StarGate-Research-Windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\StarGate.exe
[Files]
Source: "..\..\dist\StarGate\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\StarGate"; Filename: "{app}\StarGate.exe"
[Run]
Filename: "{app}\StarGate.exe"; Description: "Buka StarGate"; Flags: nowait postinstall skipifsilent unchecked
; No UninstallDelete: user data, PostgreSQL, photos, models outside bundle and backups remain.
