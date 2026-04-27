[Setup]
AppName=JARVIS2
AppVersion=1.0.0
AppPublisher=Ruben Diaz
DefaultDirName=C:\JARVIS2
DefaultGroupName=JARVIS2
OutputDir=C:\JARVIS2\installer
OutputBaseFilename=JARVIS2_Setup
Compression=lzma
SolidCompression=yes
DisableDirPage=yes

[Files]
Source: "C:\JARVIS2\jarvis.exe";   DestDir: "{app}"; Flags: ignoreversion
Source: "C:\JARVIS2\jarvis.ps1";   DestDir: "{app}"; Flags: ignoreversion
Source: "C:\JARVIS2\launcher.py";  DestDir: "{app}"; Flags: ignoreversion
Source: "C:\JARVIS2\system.md";    DestDir: "{app}"; Flags: ignoreversion
Source: "C:\JARVIS2\config.yaml";  DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
Source: "C:\JARVIS2\setup.ps1";    DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\JARVIS2"; Filename: "{app}\jarvis.exe"

[Run]
Filename: "pwsh.exe"; Parameters: "-NoExit -ExecutionPolicy Bypass -File ""{app}\setup.ps1"""; Description: "Configurar JARVIS2 (instalar dependencias)"; Flags: postinstall runasoriginaluser
