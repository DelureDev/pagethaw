param([string]$Docx,[string]$Pdf,[string]$State,[string]$Method='export')
$ErrorActionPreference='Stop'
$data=@{phase='starting';status='running';docx=$Docx;pdf=$Pdf}
function Save-State {
    $nextState=$State+'.next'
    [IO.File]::WriteAllText($nextState,($data | ConvertTo-Json),[Text.UTF8Encoding]::new($true))
    if (Test-Path -LiteralPath $State) { [IO.File]::Replace($nextState,$State,($State+'.previous')) }
    else { [IO.File]::Move($nextState,$State) }
}
Save-State
$previous=@(Get-Process WINWORD -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$word=$null
$owned=$false
try {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class WordProcessIdentity {
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
}
'@
    $word=New-Object -ComObject Word.Application
    if ($word.Documents.Count -ne 0) { throw 'Word returned an instance containing documents.' }
    $identityDocument=$word.Documents.Add()
    [uint32]$wordProcessId=0
    $null=[WordProcessIdentity]::GetWindowThreadProcessId([IntPtr]$identityDocument.ActiveWindow.Hwnd,[ref]$wordProcessId)
    $process=Get-Process -Id $wordProcessId
    if ($previous -contains $wordProcessId -or $process.ProcessName -ne 'WINWORD') {
        $identityDocument.Close(0)
        throw 'Word returned an existing process; refusing to take ownership.'
    }
    $owned=$true
    $data.word_pid=$wordProcessId
    $data.word_started=$process.StartTime.ToUniversalTime().ToString('o')
    $data.phase='opening';Save-State
    $identityDocument.Close(0)
    $word.Visible=$false;$word.DisplayAlerts=0
    $document=$word.Documents.Open($Docx,$false,$true)
    $data.phase='exporting';Save-State
    if ($Method -eq 'saveas') { $document.SaveAs2($Pdf,17) }
    else { $document.ExportAsFixedFormat($Pdf,17) }
    $data.phase='closing';Save-State
    $document.Close(0)
    $data.status='passed'
} catch { $data.status='failed';$data.error=$_.Exception.Message }
finally {
    try { Save-State }
    finally { if ($owned -and $null -ne $word) { $word.Quit() } }
}
$data.phase='finished';Save-State
if ($data.status -ne 'passed') { exit 1 }
