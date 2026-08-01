#preproc ispp

#define EnvironmentVersion GetEnv("FOCUSREADER_VERSION")
#if EnvironmentVersion != ""
  #define AppVersion EnvironmentVersion
#else
  #define AppVersion "0.1.0"
#endif
#define AppResourceVersion AppVersion + ".0"

#define AppName "FocusReader"
#define AppExeName "FocusReader.Windows.exe"
#define AppPublisher "Danzel Serrano"
#define AppUrl "https://danzelserrano.com/focusreader"

[Setup]
AppId=FocusReader.Windows
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
AppUpdatesURL={#AppUrl}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
SourceDir=..\artifacts\windows-x64
OutputDir=..\artifacts
OutputBaseFilename=FocusReader-{#AppVersion}-windows-x64-setup
UninstallDisplayIcon={app}\{#AppExeName}
AppMutex=Local\FocusReader.Windows.SingleInstance
CloseApplications=yes
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion={#AppResourceVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} installer
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppResourceVersion}

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
