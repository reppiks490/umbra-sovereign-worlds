$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$private=Join-Path $PSScriptRoot 'private-pilot'
$sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$acl=Get-Acl -LiteralPath $private
if (!$acl.AreAccessRulesProtected) { throw 'Private directory ACL is not protected' }
$bad=@($acl.Access | Where-Object { $_.AccessControlType -eq 'Allow' -and $_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value -notin @($sid,'S-1-5-18') })
if ($bad.Count -ne 0) { throw 'Unexpected allow rules' }
if ((Get-PSDrive C).Free -lt 5GB) { throw 'Training stopped: storage guard' }
$log=Join-Path $private ('training-v35-'+(Get-Date -Format 'yyyy-MM-dd')+'.log')
$python=Join-Path $PSScriptRoot '.training-venv\Scripts\python.exe'
"UTC $((Get-Date).ToUniversalTime().ToString('o'))" | Add-Content -LiteralPath $log
. (Join-Path $PSScriptRoot 'evolution_native_log_v87.ps1')
$os=Get-CimInstance Win32_OperatingSystem
if($os.FreePhysicalMemory/1024 -lt 3500 -or $os.FreeVirtualMemory/1024 -lt 6000) {
    'DEFERRED: research training memory admission' | Add-Content -LiteralPath $log
    exit 0
}
$workers=@(Get-ScheduledTask | Where-Object TaskName -eq 'MYRIAD-Research-Local-Model-Hourly')
if($workers.Count -ne 1 -or $workers[0].State -ne 'Ready') {
    'DEFERRED: local inference schedule not idle' | Add-Content -LiteralPath $log
    exit 0
}
$code=Invoke-ResearchNativeLogged -Executable $python -Arguments @('evolution_fresh_training_v35.py','--root',(Join-Path $private 'fresh-v34'),'--agents','8','--steps','128','--authorize-synthetic-training') -Log $log
if ($code -ne 0) { throw "Research training failed with native exit $code" }
