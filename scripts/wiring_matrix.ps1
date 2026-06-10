# Wiring executor matrix (Phase 0, gameplan 2026-06-10-harness-truth-and-release-ritual).
#
# Runs every candidate SessionStart command shape under the three executors a
# Windows harness may use to spawn hooks — Git Bash (bash -c), cmd.exe (/c),
# and PowerShell (direct expression) — and reports, per cell, whether the
# [Clauderizer] digest actually arrived on stdout (in-band criterion, L-09;
# exit codes are not trusted: the wrapper always exits 0).
#
# The CURRENT (known-broken-under-Git-Bash) shape stays in the matrix as the
# control proving the harness detects the failure it exists to detect (D1).
#
# Host-side by necessity: pytest-in-WSL cannot spawn Windows executors.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\wiring_matrix.ps1

param(
    [string]$Distro = 'ubuntu',
    [string]$HookPath = '/home/ccusce/Clauderizer/.clauderizer/hook.sh',
    [string]$GitBash = 'C:\Program Files\Git\bin\bash.exe',
    # Hostile-by-default: cmd.exe cannot hold a UNC cwd (falls back to
    # C:\Windows), and the engine hook discovers its repo from cwd — so a
    # shape only counts as PASS if the digest arrives WITHOUT inheriting the
    # project cwd. Run against a self-anchoring wrapper (see Phase 0 notes).
    [string]$WorkDir = 'C:\'
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Continue'
Push-Location $WorkDir

$shapes = [ordered]@{
    'CUR' = "wsl.exe -d $Distro /bin/sh $HookPath"
    'A'   = "wsl.exe -d $Distro sh -c 'exec $HookPath'"
    'B'   = "MSYS_NO_PATHCONV=1 wsl.exe -d $Distro /bin/sh $HookPath"
    'C'   = "wsl.exe -d $Distro //bin/sh /$HookPath"
}

function Invoke-Cell {
    param([string]$Executor, [string]$Command)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $out = ''
    $exit = 'n/a'
    try {
        switch ($Executor) {
            'gitbash' { $out = (& $GitBash -c $Command 2>&1 | Out-String); $exit = $LASTEXITCODE }
            'cmd'     { $out = (& $env:ComSpec /d /c $Command 2>&1 | Out-String); $exit = $LASTEXITCODE }
            'ps'      { $out = (Invoke-Expression "$Command 2>&1" | Out-String); $exit = $LASTEXITCODE }
        }
    } catch {
        $out = $_.Exception.Message
        $exit = 'exception'
    }
    $sw.Stop()
    $digest = $out -match '\[Clauderizer\]'
    $first = ($out -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1)
    if ($null -eq $first) { $first = '(no output)' }
    if ($first.Length -gt 110) { $first = $first.Substring(0, 110) + '…' }
    [pscustomobject]@{
        Executor = $Executor
        Digest   = $digest
        Exit     = $exit
        Ms       = $sw.ElapsedMilliseconds
        First    = $first.Trim()
    }
}

$executors = @('gitbash', 'cmd', 'ps')
$results = @()
foreach ($name in $shapes.Keys) {
    $cmd = $shapes[$name]
    Write-Output "=== shape $name :: $cmd"
    foreach ($ex in $executors) {
        $r = Invoke-Cell -Executor $ex -Command $cmd
        $results += [pscustomobject]@{ Shape = $name; Executor = $ex; Digest = $r.Digest; Exit = $r.Exit; Ms = $r.Ms; First = $r.First }
        Write-Output ("  {0,-8} digest={1,-5} exit={2,-9} {3,5}ms  {4}" -f $ex, $r.Digest, $r.Exit, $r.Ms, $r.First)
    }
}

Write-Output ''
Write-Output '=== MATRIX (digest arrived in-band) ==='
foreach ($name in $shapes.Keys) {
    $row = $results | Where-Object { $_.Shape -eq $name }
    $cells = foreach ($ex in $executors) { $c = $row | Where-Object { $_.Executor -eq $ex }; if ($c.Digest) { 'PASS' } else { 'FAIL' } }
    Write-Output ("{0,-4} gitbash={1} cmd={2} ps={3}" -f $name, $cells[0], $cells[1], $cells[2])
}

$winners = @()
foreach ($name in $shapes.Keys) {
    $row = $results | Where-Object { $_.Shape -eq $name }
    if (-not ($row | Where-Object { -not $_.Digest })) { $winners += $name }
}
Write-Output ''
if ($winners.Count -gt 0) {
    Write-Output ("ELIGIBLE (digest under ALL executors): {0}" -f ($winners -join ', '))
} else {
    Write-Output 'ELIGIBLE: none — escalate per D1 (no shape passed all three executors)'
}
Pop-Location
