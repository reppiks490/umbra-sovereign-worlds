function Invoke-ResearchNativeLogged {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Executable,[Parameter(Mandatory=$true)][string[]]$Arguments,[Parameter(Mandatory=$true)][string]$Log)
    if(!(Test-Path -LiteralPath $Executable -PathType Leaf)){throw 'Native executable missing'}
    # Fail before executing if log creation or append is impossible.
    $stream=[IO.File]::Open($Log,[IO.FileMode]::Append,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $writer=[IO.StreamWriter]::new($stream,[Text.UTF8Encoding]::new($false))
    $original=$ErrorActionPreference
    try {
        # Windows PowerShell 5.1 wraps native stderr as ErrorRecord. Do not
        # mistake a warning for a failed native process; use actual exit code.
        $ErrorActionPreference='Continue'
        & $Executable @Arguments 2>&1 | ForEach-Object {
            $writer.WriteLine([string]$_)
            $writer.Flush()
        }
        $code=$LASTEXITCODE
        if($null -eq $code){throw 'Native exit code unavailable'}
        return [int]$code
    } finally {
        $ErrorActionPreference=$original
        $writer.Dispose()
        $stream.Dispose()
    }
}
