# CI-only! Installs into an isolated temporary location on an ephemeral Windows runner.
# Does not run on the user's laptop and does not require administrator rights.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$installer = @(Get-ChildItem 'dist\installer\Vikora_Setup_*.exe') | Select-Object -First 1
if (-not $installer) { throw 'No Inno Setup installer found' }
$testDirectory = Join-Path $env:RUNNER_TEMP 'vikora-installer-ci'
New-Item -ItemType Directory -Force -Path $testDirectory | Out-Null
$installPath = Join-Path $testDirectory 'application'
$exe = Join-Path $installPath 'Vikora.exe'
$testProfile = Join-Path $testDirectory 'profile'

# No automatic launch in silent mode: the test starts the installed EXE explicitly.
$installArgs = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', "/DIR=`"$installPath`"")
$installResult = Start-Process -FilePath $installer.FullName -ArgumentList $installArgs -Wait -PassThru
if ($installResult.ExitCode -ne 0) { throw "Silent install failed ($($installResult.ExitCode))" }
if (-not (Test-Path $exe)) { throw 'Installed Vikora.exe not found' }
py -3.11 packaging\windows_smoke.py --exe $exe --data-dir $testProfile
if ($LASTEXITCODE -ne 0) { throw 'Installed application smoke test failed' }

# Installing an update in the same directory must not remove data: that is
# enforced by a separate data-directory persistence smoke test above.
$upgradeResult = Start-Process -FilePath $installer.FullName -ArgumentList $installArgs -Wait -PassThru
if ($upgradeResult.ExitCode -ne 0) { throw "Installer could not upgrade over existing installation ($($upgradeResult.ExitCode))" }
if (-not (Test-Path $exe)) { throw 'Upgraded EXE missing' }
py -3.11 packaging\windows_smoke.py --exe $exe --data-dir $testProfile
if ($LASTEXITCODE -ne 0) { throw 'Updated application smoke test failed' }

$uninstaller = Join-Path $installPath 'unins000.exe'
if (-not (Test-Path $uninstaller)) { throw 'Expected Windows uninstaller not found' }
$uninstallResult = Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART') -Wait -PassThru
if ($uninstallResult.ExitCode -ne 0) { throw "Uninstaller failed ($($uninstallResult.ExitCode))" }
Write-Host 'PASS: silent install / reinstall / launch / uninstall checked in CI'

# The user profile must survive uninstallation; Vikora never silently wipes HR data.
if (-not (Test-Path (Join-Path $testProfile 'vikora.sqlite3'))) {
    throw 'Uninstallation removed the synthetic user database'
}
if (-not (Test-Path (Join-Path $testProfile 'synthetic_smoke_id.txt'))) {
    throw 'Uninstallation removed the synthetic candidate marker'
}
Write-Host 'PASS: synthetic user data remains after uninstall'
