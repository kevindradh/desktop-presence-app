param([switch]$IncludeResearchModels, [string]$PostgresRuntime)
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..\..')
$Python = Join-Path (Get-Location) '.venv-win\Scripts\python.exe'
if (!(Test-Path $Python)) { throw 'Buat .venv-win menggunakan Python 3.11 x64 terlebih dahulu. Lihat docs/windows-install.md.' }
if (!$PostgresRuntime -or !(Test-Path (Join-Path $PostgresRuntime 'runtime-manifest.json'))) {
    throw 'Isi -PostgresRuntime dengan runtime PostgreSQL/pgvector yang sudah disiapkan. Lihat docs/windows-build.md.'
}
& $Python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependensi tidak konsisten.' }
$BuildArgs = @('scripts/build_package.py','--target','windows')
if ($IncludeResearchModels) { $BuildArgs += '--include-research-models' }
if ($PostgresRuntime) { $BuildArgs += @('--postgres-runtime', $PostgresRuntime) }
& $Python @BuildArgs
if ($LASTEXITCODE -ne 0) { throw 'Build gagal.' }
$ProbeArgs = @('package-check','--data-dir',"$env:TEMP\StarGate-package-probe")
if ($IncludeResearchModels) { $ProbeArgs += '--verify-models' }
& '.\dist\StarGate\StarGateAdmin.exe' @ProbeArgs
if ($LASTEXITCODE -ne 0) { throw 'Pemeriksaan paket gagal; installer tidak dibuat.' }
$Compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
$CompilerPath = if ($Compiler) { $Compiler.Source } else { $null }
if (!$CompilerPath) {
    foreach ($Candidate in @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe")) {
        if (Test-Path $Candidate) { $CompilerPath = $Candidate; break }
    }
}
if (!$CompilerPath) { throw 'Pasang Inno Setup 6 untuk menghasilkan installer. Lihat docs/windows-build.md.' }
& $CompilerPath 'packaging\windows\StarGate.iss'
if ($LASTEXITCODE -ne 0) { throw 'Compiler installer gagal.' }
Write-Host 'Installer dibuat. UAT Windows masih wajib; belum ditandatangani untuk rilis publik.'
