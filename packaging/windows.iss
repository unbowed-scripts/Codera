#ifndef AppVersion
  #define AppVersion "0.4.0"
#endif
[Setup]
AppId={{5A5C22B1-2175-4449-8E60-3866CB6F5D12}
AppName=PythonTech
AppVersion={#AppVersion}
AppPublisher=PythonTech contributors
AppPublisherURL=https://github.com/unbowed-scripts/PythonTech
DefaultDirName={localappdata}\Programs\PythonTech
DefaultGroupName=PythonTech
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installers
OutputBaseFilename=PythonTech-{#AppVersion}-windows-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\PythonTech.exe
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\PythonTech\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PythonTech"; Filename: "{app}\PythonTech.exe"
Name: "{autodesktop}\PythonTech"; Filename: "{app}\PythonTech.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PythonTech.exe"; Description: "Launch PythonTech"; Flags: nowait postinstall skipifsilent
