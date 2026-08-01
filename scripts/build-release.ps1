[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string] $Version,

    [string] $IsccPath,

    [switch] $SkipInstaller
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$artifactsPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot 'artifacts'))
$requiredPrefix = $repoRoot + [System.IO.Path]::DirectorySeparatorChar

if (-not $artifactsPath.StartsWith($requiredPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The artifacts directory resolved outside the repository.'
}

if (Test-Path -LiteralPath $artifactsPath) {
    Remove-Item -LiteralPath $artifactsPath -Recurse -Force
}

$windowsBuildPath = Join-Path $artifactsPath 'windows-build'
$windowsPublishPath = Join-Path $artifactsPath 'windows-x64'
$chromeStagePath = Join-Path $artifactsPath 'chrome-package'
New-Item -ItemType Directory -Path $windowsBuildPath, $windowsPublishPath, $chromeStagePath -Force | Out-Null

$windowsSourcePath = Join-Path $repoRoot 'windows'
$cmakeVersionArgument = "-DFOCUSREADER_VERSION=$Version"
& cmake -S $windowsSourcePath -B $windowsBuildPath $cmakeVersionArgument

if ($LASTEXITCODE -ne 0) {
    throw "CMake configuration failed with exit code $LASTEXITCODE."
}

& cmake --build $windowsBuildPath --config Release
if ($LASTEXITCODE -ne 0) {
    throw "Native C build failed with exit code $LASTEXITCODE."
}

& ctest --test-dir $windowsBuildPath -C Release --output-on-failure
if ($LASTEXITCODE -ne 0) {
    throw "Native C checks failed with exit code $LASTEXITCODE."
}

$builtExecutable = Join-Path $windowsBuildPath 'bin\FocusReader.Windows.exe'
if (-not (Test-Path -LiteralPath $builtExecutable)) {
    throw "The native build did not produce $builtExecutable."
}
Copy-Item -LiteralPath $builtExecutable -Destination $windowsPublishPath

$chromeRoot = Join-Path $repoRoot 'chrome'
Copy-Item -LiteralPath (Join-Path $chromeRoot 'manifest.json') -Destination $chromeStagePath
Copy-Item -LiteralPath (Join-Path $chromeRoot 'src') -Destination $chromeStagePath -Recurse

$stagedManifestPath = Join-Path $chromeStagePath 'manifest.json'
$manifest = Get-Content -LiteralPath $stagedManifestPath -Raw | ConvertFrom-Json
$manifest.version = $Version
$manifest.version_name = $Version
$manifestJson = $manifest | ConvertTo-Json -Depth 100
[System.IO.File]::WriteAllText(
    $stagedManifestPath,
    $manifestJson + [Environment]::NewLine,
    [System.Text.UTF8Encoding]::new($false)
)

$chromeZipPath = Join-Path $artifactsPath "FocusReader-$Version-chrome.zip"
Compress-Archive -Path (Join-Path $chromeStagePath '*') -DestinationPath $chromeZipPath

$portableZipPath = Join-Path $artifactsPath "FocusReader-$Version-windows-x64-portable.zip"
Compress-Archive -Path (Join-Path $windowsPublishPath '*') -DestinationPath $portableZipPath

if (-not $SkipInstaller) {
    if (-not $IsccPath) {
        $isccCommand = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($isccCommand) {
            $IsccPath = $isccCommand.Source
        }
    }

    if (-not $IsccPath) {
        $isccCandidates = @(
            (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
        )
        $IsccPath = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }

    if (-not $IsccPath -or -not (Test-Path -LiteralPath $IsccPath)) {
        throw 'Inno Setup 6 was not found. Install it with: winget install --id JRSoftware.InnoSetup -e --scope user'
    }

    $installerScript = Join-Path $repoRoot 'installer\FocusReader.iss'
    $env:FOCUSREADER_VERSION = $Version
    & $IsccPath "/O$artifactsPath" "/FFocusReader-$Version-windows-x64-setup" $installerScript

    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
    }
}

Remove-Item -LiteralPath $chromeStagePath -Recurse -Force
Remove-Item -LiteralPath $windowsPublishPath -Recurse -Force
Remove-Item -LiteralPath $windowsBuildPath -Recurse -Force

$checksumPath = Join-Path $artifactsPath 'SHA256SUMS.txt'
$checksumLines = Get-ChildItem -LiteralPath $artifactsPath -File |
    Where-Object { $_.Name -ne 'SHA256SUMS.txt' } |
    Sort-Object Name |
    ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $($_.Name)"
    }

[System.IO.File]::WriteAllLines(
    $checksumPath,
    $checksumLines,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Release artifacts created in $artifactsPath"
Get-ChildItem -LiteralPath $artifactsPath -File | Select-Object Name, Length
