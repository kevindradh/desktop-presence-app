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
Filename: "{app}\StarGate.exe"; Description: "Buka StarGate"; Flags: nowait postinstall skipifsilent; Check: CanLaunch
[UninstallRun]
Filename: "{app}\StarGateAdmin.exe"; Parameters: "stop-local-db"; Flags: runhidden waituntilterminated skipifdoesntexist
[Code]
var
  LocalSetupReady: Boolean;

function InitializeSetup(): Boolean;
begin
  LocalSetupReady := True;
  Result := True;
end;

function CanLaunch(): Boolean;
begin
  Result := LocalSetupReady;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExitCode: Integer;
begin
  if (CurStep = ssPostInstall) and FileExists(ExpandConstant('{app}\_internal\postgresql\runtime-manifest.json')) then
  begin
    WizardForm.StatusLabel.Caption := 'Menyiapkan database StarGate...';
    LocalSetupReady := Exec(ExpandConstant('{app}\StarGateAdmin.exe'), 'setup-local',
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ExitCode);
    if LocalSetupReady then
      LocalSetupReady := ExitCode = 0;
    if LocalSetupReady then
    begin
      WizardForm.StatusLabel.Caption := 'Memeriksa aplikasi StarGate...';
      if FileExists(ExpandConstant('{app}\_internal\resources\models\w600k_r50.onnx')) then
        LocalSetupReady := Exec(ExpandConstant('{app}\StarGateAdmin.exe'), 'package-check --verify-models',
          ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ExitCode)
      else
        LocalSetupReady := Exec(ExpandConstant('{app}\StarGateAdmin.exe'), 'package-check',
          ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ExitCode);
      if LocalSetupReady then
        LocalSetupReady := ExitCode = 0;
    end;
    if not LocalSetupReady then
      MsgBox('Setup awal belum selesai. Data tetap disimpan. Hubungi pendamping pengujian sebelum membuka StarGate.', mbError, MB_OK);
  end;
end;
; No UninstallDelete: user data, PostgreSQL, photos, models outside bundle and backups remain.
