# Run the same test_*.py module set as unittest discovery, in fresh sequential
# processes so resolved-rule caches cannot accumulate across the entire suite.
[CmdletBinding()]
param(
    [ValidateRange(64,4096)][int]$MaxMemoryMB = 1024,
    [ValidateRange(1,90)][int]$MaxSystemMemoryPercent = 88,
    [ValidateRange(1,1800)][int]$ModuleTimeoutSeconds = 180,
    [ValidateRange(1,3600)][int]$TotalTimeoutSeconds = 1200,
    [string]$Pattern = 'test_*.py'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$modules = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'tests') -Filter $Pattern -File | Sort-Object Name)
if ($modules.Count -eq 0) { throw 'No matching test modules.' }
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$rows = [System.Collections.Generic.List[object]]::new()
$totalTests = 0
$skipped = 0
$peakMB = 0.0
$peakSystemPercent = 0.0
Push-Location $repoRoot
try {
    foreach ($module in $modules) {
        $remaining = $TotalTimeoutSeconds - [int]$timer.Elapsed.TotalSeconds
        if ($remaining -le 0) { break }
        $moduleLimit = [Math]::Min($ModuleTimeoutSeconds, $remaining)
        $log = (& (Join-Path $PSScriptRoot 'run-bounded-python.ps1') -PythonArguments @('-m','unittest','discover','-s','tools/tests','-p',$module.Name,'-q') -MaxMemoryMB $MaxMemoryMB -MaxSystemMemoryPercent $MaxSystemMemoryPercent -TimeoutSeconds $moduleLimit) -join "`n"
        $resultCode = $LASTEXITCODE
        $ran = [regex]::Matches($log, 'Ran (\d+) tests? in')
        $count = if ($ran.Count) { [int]$ran[-1].Groups[1].Value } else { 0 }
        $skipMatch = [regex]::Match($log, 'skipped=(\d+)')
        $skipCount = if ($skipMatch.Success) { [int]$skipMatch.Groups[1].Value } else { 0 }
        $peak = [regex]::Match($log, 'sampled tree peak ([0-9.]+) MB')
        if ($peak.Success) { $peakMB = [Math]::Max($peakMB, [double]::Parse($peak.Groups[1].Value,[cultureinfo]::InvariantCulture)) }
        $pcPeak = [regex]::Match($log, 'PC memory peak: ([0-9.]+)%')
        if ($pcPeak.Success) { $peakSystemPercent = [Math]::Max($peakSystemPercent, [double]::Parse($pcPeak.Groups[1].Value,[cultureinfo]::InvariantCulture)) }
        $totalTests += $count
        $skipped += $skipCount
        $rows.Add([ordered]@{module=$module.Name; exit_code=$resultCode; tests=$count; skipped=$skipCount; output=$log})
        Write-Output ("{0}: exit {1}; {2} tests; {3} skipped" -f $module.Name,$resultCode,$count,$skipCount)
        if ($resultCode -ne 0) { Write-Output $log }
    }
    $failures = @($rows | Where-Object { $_.exit_code -ne 0 }).Count
    $complete = $rows.Count -eq $modules.Count
    $report = [ordered]@{
        mode='sequential isolated unittest modules; not one-process discovery'
        pattern=$Pattern; expected_modules=$modules.Count; completed_modules=$rows.Count
        complete=$complete; failed_modules=$failures; tests_run=$totalTests; skipped=$skipped
        sampled_peak_tree_mb=$peakMB; elapsed_seconds=[Math]::Round($timer.Elapsed.TotalSeconds,1)
        memory_limit_mb=$MaxMemoryMB; module_timeout_seconds=$ModuleTimeoutSeconds
        system_memory_limit_percent=$MaxSystemMemoryPercent; sampled_peak_system_memory_percent=$peakSystemPercent
        modules=$rows
    }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $repoRoot 'docs/audit/latest/bounded_test_run.json') -Encoding utf8
    Write-Output ("TOTAL: {0}/{1} modules; {2} tests; {3} skipped; {4} failed modules; sampled peak {5} MB" -f $rows.Count,$modules.Count,$totalTests,$skipped,$failures,$peakMB)
    if (-not $complete -or $failures -gt 0) { exit 1 }
} finally {
    Pop-Location
}
