# Run a small Python check with sampled process-tree memory and elapsed-time guards.
# This is not an OS hard allocation limit: the tree is sampled every 200 ms.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string[]]$PythonArguments,
    [ValidateRange(64, 4096)][int]$MaxMemoryMB = 1024,
    [ValidateRange(1, 90)][int]$MaxSystemMemoryPercent = 88,
    [ValidateRange(1, 1800)][int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$pythonPath = (Get-Command python -CommandType Application | Select-Object -First 1).Source
$startInfo = [System.Diagnostics.ProcessStartInfo]::new($pythonPath)
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.WorkingDirectory = (Get-Location).Path
foreach ($argument in $PythonArguments) { $startInfo.ArgumentList.Add($argument) }
$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $startInfo
$timer = [System.Diagnostics.Stopwatch]::StartNew()
$peakBytes = 0L
$peakSystemPercent = 0.0
$failure = $null
$started = $false
$tracked = [System.Collections.Generic.Dictionary[int, System.Diagnostics.Process]]::new()
try {
    $osMemory = Get-CimInstance Win32_OperatingSystem
    $initialPercent = 100 * (1 - $osMemory.FreePhysicalMemory / $osMemory.TotalVisibleMemorySize)
    if ($initialPercent -ge $MaxSystemMemoryPercent) {
        throw "PC memory usage already exceeds the ${MaxSystemMemoryPercent}% safety threshold."
    }
    [void]$process.Start()
    $started = $true
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $tracked.Add($process.Id, $process)
    do {
        # Keep watching after root exit: a child may still own a redirected pipe.
        Start-Sleep -Milliseconds 200
        $allProcesses = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId)
        do {
            $added = $false
            foreach ($entry in $allProcesses) {
                if ($tracked.ContainsKey([int]$entry.ParentProcessId) -and -not $tracked.ContainsKey([int]$entry.ProcessId)) {
                    $child = Get-Process -Id $entry.ProcessId -ErrorAction SilentlyContinue
                    if ($child -and $child.StartTime -ge $process.StartTime) {
                        [void]$child.Handle # Retain a handle, not only a reusable PID.
                        $tracked.Add([int]$entry.ProcessId, $child)
                        $added = $true
                    }
                }
            }
        } while ($added)
        $bytes = 0L
        $anyAlive = $false
        foreach ($observed in $tracked.Values) {
            $observed.Refresh()
            if (-not $observed.HasExited) {
                $anyAlive = $true
                $bytes += $observed.PrivateMemorySize64
            }
        }
        $peakBytes = [Math]::Max($peakBytes, $bytes)
        $osMemory = Get-CimInstance Win32_OperatingSystem
        $systemPercent = 100 * (1 - $osMemory.FreePhysicalMemory / $osMemory.TotalVisibleMemorySize)
        $peakSystemPercent = [Math]::Max($peakSystemPercent, $systemPercent)
        if ($bytes -gt $MaxMemoryMB * 1MB) { $failure = "memory exceeded ${MaxMemoryMB} MB" }
        if ($systemPercent -ge $MaxSystemMemoryPercent) { $failure = "PC memory reached the ${MaxSystemMemoryPercent}% safety threshold" }
        if ($timer.Elapsed.TotalSeconds -gt $TimeoutSeconds) { $failure = "timeout exceeded ${TimeoutSeconds}s" }
        if ($failure) {
            foreach ($observed in $tracked.Values) {
                if (-not $observed.HasExited) { $observed.Kill($true) }
            }
            break
        }
    } while ($anyAlive -or -not $stdout.IsCompleted -or -not $stderr.IsCompleted)
    [void]$process.WaitForExit(5000)
    # Never block forever draining a pipe after a guard failure. Extremely short-
    # lived intermediary parents can evade sampled ancestry discovery; this is
    # not a sandbox or a hard OS job-object limit.
    if ($stdout.Wait(5000)) { Write-Output $stdout.GetAwaiter().GetResult() }
    $errorText = if ($stderr.Wait(5000)) { $stderr.GetAwaiter().GetResult() } else { 'Output drain incomplete after termination.' }
    if ($errorText) { Write-Output $errorText }
    Write-Output ([string]::Format([cultureinfo]::InvariantCulture, 'Bounded Python: sampled tree peak {0:F1} MB; elapsed {1:F1}s; exit {2}', ($peakBytes / 1MB), $timer.Elapsed.TotalSeconds, $process.ExitCode))
    Write-Output ([string]::Format([cultureinfo]::InvariantCulture, 'Sampled PC memory peak: {0:F1}%', $peakSystemPercent))
    if ($failure) {
        Write-Output "STOPPED: $failure"
        exit 124
    }
    exit $process.ExitCode
} finally {
    foreach ($observed in $tracked.Values) {
        if (-not $observed.HasExited) { $observed.Kill($true) }
        if ($observed -ne $process) { $observed.Dispose() }
    }
    if ($started -and -not $process.HasExited) { $process.Kill($true) }
    $process.Dispose()
}
