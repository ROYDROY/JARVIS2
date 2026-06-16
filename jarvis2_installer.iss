[Setup]
AppName=JARVIS2
AppVersion=4.0.0
AppPublisher=Ruben Diaz
DefaultDirName=C:\JARVIS2
DefaultGroupName=JARVIS2
OutputDir=C:\JARVIS2\installer
OutputBaseFilename=JARVIS2_Setup
Compression=lzma
SolidCompression=yes
DisableDirPage=yes

[Dirs]
Name: "{app}\memoria"
Name: "{app}\logs"
Name: "{app}\sandbox"
Name: "{app}\modulos"
Name: "{app}\herramientas"

[Files]
Source: "C:\JARVIS2\jarvis_app.py";               DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\gui.py";                      DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\proactivo.py";                 DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\procesar_sesion.py";          DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\config.yaml";                 DestDir: "{app}";          Flags: ignoreversion onlyifdoesntexist
Source: "C:\JARVIS2\system.md";                   DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\setup.ps1";                   DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\lanzar_jarvis.bat";            DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\lanzar_silencioso.vbs";        DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\Manual_Usuario_JARVIS.pdf";     DestDir: "{app}";          Flags: ignoreversion
Source: "C:\JARVIS2\herramientas\*";              DestDir: "{app}\herramientas"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\JARVIS2\modulos\indice.psm1";        DestDir: "{app}\modulos"; Flags: ignoreversion
Source: "C:\JARVIS2\memoria\memoria.json";       DestDir: "{app}\memoria"; Flags: ignoreversion onlyifdoesntexist
Source: "C:\JARVIS2\memoria\indice.json";        DestDir: "{app}\memoria"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{userdesktop}\JARVIS2"; Filename: "{app}\lanzar_silencioso.vbs"

[Run]
Filename: "powershell.exe"; Parameters: "-NoExit -ExecutionPolicy Bypass -File ""{app}\setup.ps1"""; Description: "Configurar JARVIS2 (instalar dependencias)"; Flags: postinstall runasoriginaluser
