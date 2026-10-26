param(
    [Parameter(Mandatory=$true)][string]$Release,
    [Parameter(Mandatory=$true)][string]$Results,
    [switch]$FreshRunner
)
$ErrorActionPreference = 'Stop'
$releasePath = (Resolve-Path -LiteralPath $Release).Path
$resultsPath = [IO.Path]::GetFullPath($Results)
if (Test-Path -LiteralPath $resultsPath) { throw 'Choose a new results folder.' }
New-Item -ItemType Directory -Path $resultsPath | Out-Null
$single = @(Get-ChildItem -LiteralPath $releasePath -Filter 'PageThaw-*-windows-x64.exe')
$zip = @(Get-ChildItem -LiteralPath $releasePath -Filter 'PageThaw-*-windows-x64.zip')
if ($single.Count -ne 1 -or $zip.Count -ne 1) { throw 'Expected one EXE and one ZIP.' }
foreach ($line in Get-Content -LiteralPath (Join-Path $releasePath 'SHA256SUMS.txt')) {
    if ($line -notmatch '^([a-f0-9]{64})  (PageThaw-[^\\/]+)$') { throw 'Invalid checksum entry.' }
    $actual = (Get-FileHash -LiteralPath (Join-Path $releasePath $Matches[2]) -Algorithm SHA256).Hash
    if ($actual -ne $Matches[1]) { throw 'Artifact checksum mismatch.' }
}
$work = Join-Path $resultsPath 'Portable проверка'
New-Item -ItemType Directory -Path $work | Out-Null
Copy-Item -LiteralPath $single[0].FullName -Destination (Join-Path $work 'PageThaw.exe')
Expand-Archive -LiteralPath $zip[0].FullName -DestinationPath (Join-Path $work 'folder')
$oldPath = $env:PATH
$oldLocal = $env:LOCALAPPDATA
$removed = @{}
Get-ChildItem Env: | Where-Object { $_.Name -like 'PYTHON*' -or $_.Name -eq 'VIRTUAL_ENV' } | ForEach-Object {
    $removed[$_.Name] = $_.Value
    [Environment]::SetEnvironmentVariable($_.Name, $null, 'Process')
}
try {
    # The Python launcher can live in the Windows root on hosted images.
    # Keep only System32; the app must use its bundled interpreter.
    $env:PATH = "$env:SystemRoot\System32"
    $env:LOCALAPPDATA = Join-Path $work 'clean-profile'
    New-Item -ItemType Directory -Path $env:LOCALAPPDATA | Out-Null
    $external = @(Get-Command python, python3, py -CommandType Application -ErrorAction SilentlyContinue)
    if ($external.Count) { throw ('External Python is still available on PATH: '+($external.Source -join ', ')) }
    if ($FreshRunner) {
        if ($env:GITHUB_ACTIONS -ne 'true') { throw 'FreshRunner is only valid on an ephemeral GitHub runner.' }
        if (Test-Path 'Registry::HKEY_CLASSES_ROOT\Word.Application') { throw 'Word is installed on this runner.' }
        if (Get-ChildItem -LiteralPath "$env:SystemRoot\Fonts" | Where-Object Name -Match 'Sirius') { throw 'Private fonts found on runner.' }
    }
    $binaries = @{
        single = (Join-Path $work 'PageThaw.exe')
        folder = (Join-Path $work 'folder\PageThaw\PageThaw.exe')
    }
    $checks = @{}
    foreach ($kind in @('single', 'folder')) {
        $out = Join-Path $work ('smoke-'+$kind)
        $process = Start-Process -FilePath $binaries[$kind] -ArgumentList @('--self-test', ('"'+$out+'"')) -WorkingDirectory $work -PassThru -WindowStyle Hidden
        if (-not $process.WaitForExit(120000)) { Stop-Process -Id $process.Id; throw "$kind smoke timed out." }
        if ($process.ExitCode -ne 0) {
            $errorFile = Join-Path $out 'self-test-error.txt'
            if (Test-Path -LiteralPath $errorFile) { Get-Content -LiteralPath $errorFile }
            throw "$kind smoke failed: $($process.ExitCode)"
        }
        $report = Get-Content -Raw -LiteralPath (Join-Path $out 'smoke-result.json') | ConvertFrom-Json
        if ($report.field_geometry -ne 'passed') { throw "$kind field geometry verification failed." }
        if ($report.status -ne 'passed' -or -not $report.frozen -or $report.bundled_runtime -ne 'passed' -or $report.gui -ne 'passed' -or $report.retained_lines -ne 'passed' -or $report.native_footnotes -ne 'passed' -or $report.touching_blank_border -ne 'passed') { throw "$kind runtime verification failed." }
        $checks[$kind] = $report
    }
    $notices = Join-Path $work 'notices'
    $process = Start-Process -FilePath $binaries.single -ArgumentList @('--export-notices', ('"'+$notices+'"')) -WorkingDirectory $work -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit(60000)) { Stop-Process -Id $process.Id; throw 'Notices export timed out.' }
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $notices 'DEPENDENCY_SOURCES.json'))) { throw 'Notices export failed.' }
    @{ status='passed'; fresh_github_vm=[bool]$FreshRunner; external_python_on_path=$false; word_required=$false; checks=$checks } |
        ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $resultsPath 'portable-result.json')
    Write-Output 'Both portable formats passed, including repeat conversion, DOCX-only output, bundled runtime and EN/RU GUI.'
} finally {
    $env:PATH = $oldPath
    $env:LOCALAPPDATA = $oldLocal
    foreach ($name in $removed.Keys) { [Environment]::SetEnvironmentVariable($name, $removed[$name], 'Process') }
}
