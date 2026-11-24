param([string]$Python='python')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'evolution_native_log_v87.ps1')
$p=Join-Path $PSScriptRoot ('test-'+[Guid]::NewGuid().ToString('N')+'.log')
try {
  $r=Invoke-ResearchNativeLogged -Executable $Python -Arguments @('-c',"import sys;sys.stderr.write('synthetic warning\n');print('success')") -Log $p
  if($r -ne 0){throw 'Warning should not terminate successful process'}
  $s=Get-Content -LiteralPath $p -Raw
  if($s -notmatch 'synthetic warning' -or $s -notmatch 'success'){throw 'Both streams must be preserved'}
  $r=Invoke-ResearchNativeLogged -Executable $Python -Arguments @('-c',"import sys;sys.stderr.write('synthetic failure\n');sys.exit(7)") -Log $p
  if($r -ne 7){throw 'Native failure must retain exit status'}
  if((Get-Content -LiteralPath $p -Raw) -notmatch 'synthetic failure'){throw 'Failure diagnostic missing'}
  if($ErrorActionPreference -ne 'Stop'){throw 'Caller preference changed'}
  $caught=$false
  try { Invoke-ResearchNativeLogged -Executable $Python -Arguments @('-c',"print('must not execute')") -Log (Join-Path $p 'missing.log') | Out-Null } catch { $caught=$true }
  if(!$caught){throw 'Invalid log destination must fail closed'}
  'PASS: streams, warning, native exit, preference, log failure'
} finally {if(Test-Path $p){Remove-Item -LiteralPath $p}}
# All assertions and cleanup completed; do not leak the intentional native exit 7.
exit 0
