param([string]$State)
$ErrorActionPreference='Stop'
$data=Get-Content -LiteralPath $State -Raw | ConvertFrom-Json
if ($data.word_pid -and $data.word_started) {
    $process=Get-Process -Id $data.word_pid -ErrorAction SilentlyContinue
    if ($process -and $process.ProcessName -eq 'WINWORD' -and
        $process.StartTime.ToUniversalTime().ToString('o') -eq $data.word_started) {
        Stop-Process -Id $process.Id
    }
}
