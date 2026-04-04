; LaTaverneAI Installation Script
; Nécessite Inno Setup Compiler
; Configuration pour installation locale sans droits administrateur (User-mode)

#define MyAppName "LaTaverneAI"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Timéo (Veyler)"
#define MyAppURL "https://github.com/Veyler/-LaTaverneAI-"
#define MyAppExeName "[LaTaverneAI].exe"

[Setup]
; Identifiant unique pour désinstallation même si la version change
AppId={{5F7C38B2-A8A2-4DFA-BC76-E1E0F4E8D7CA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation en mode utilisateur (Local AppData) pour permettre les mises à jour auto sans UAC Admin
PrivilegesRequired=lowest
DefaultDirName={localappdata}\{#MyAppName}
DisableProgramGroupPage=yes

; Fichiers générés
OutputDir=dist
OutputBaseFilename=LaTaverneAI_Setup
SetupIconFile=icons\icon128x128.ico
Compression=lzma
SolidCompression=yes

; Esthétique
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; L'exécutable PyInstaller généré (doit être compilé AVANT de lancer InnoSetup)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Si besoin d'autres fichiers, les rajouter ici. (Icones incluses dans l'exe standalone pyinstaller logiquement)
Source: "icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
