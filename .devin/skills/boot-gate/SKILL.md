---
name: boot-gate
description: "Boot-gate the game before committing: launch, verify menu, check for exceptions"
triggers:
  - user
  - model
---

# Boot-Gate — verify the game reaches the main menu before committing

This skill runs the full Cameo boot-gate procedure. **Never commit engine content
(mods/, OpenRA.Mods.Cameo/, engine/) without running this first.**

## Procedure

1. **Snapshot the exception log list BEFORE launching** so you can detect NEW exceptions:
   ```powershell
   $logDir = "$env:APPDATA\OpenRA\Logs"
   $before = Get-ChildItem "$logDir\exception-*.log" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
   ```

2. **Launch the game:**
   ```powershell
   .\launch-game.cmd
   ```
   Wait for it to reach the main menu. This takes 30-90 seconds depending on the machine.

3. **Verify menu was reached** by checking perf.log ends with `MenuPostProcessEffect.PostWorldLoaded`:
   ```powershell
   $perf = Get-Content "$env:APPDATA\OpenRA\Logs\perf.log" -Tail 40
   $perf | Select-String "MenuPostProcessEffect.PostWorldLoaded"
   ```
   If this string is NOT found in the last 40 lines, the boot FAILED.

4. **Check for NEW exception logs:**
   ```powershell
   $after = Get-ChildItem "$logDir\exception-*.log" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
   $new = $after | Where-Object { $_ -notin $before }
   if ($new) { Write-Error "NEW exception logs found: $($new -join ', ')" }
   ```
   If any new exception-*.log files appeared, the boot FAILED. Read them to diagnose.

5. **Kill the game process** after verification — **PID-scoped only.**
   Multiple agents share this machine; `Stop-Process -Name OpenRA` or
   `taskkill /IM OpenRA.exe` sweeps EVERY lane's live matches.
   Track your launch PID and kill only processes whose path is inside
   THIS worktree:
   ```powershell
   # Preferred: keep the PID from your launch and kill it directly:
   Stop-Process -Id $gamePid -Force -ErrorAction SilentlyContinue

   # Fallback: scope by executable path — never by image name:
   Get-Process -Name "OpenRA*","dotnet" -ErrorAction SilentlyContinue |
     Where-Object { $_.Path -like "$PWD*" -or $_.Path -like "$PWD\engine*" } |
     Stop-Process -Force
   ```

## Pre-conditions

- If C# sources changed (`OpenRA.Mods.Cameo/` or `engine/`), rebuild FIRST:
  ```powershell
  $env:DOTNET_ROLL_FORWARD="LatestMajor"
  dotnet build -c Release --nologo -p:TargetPlatform=win-x64
  ```
  Stale DLLs crash with `Cannot locate type: ...Info`.

- If Windows Smart App Control (SAC) blocks the binaries, see `docs/LESSONS_LEARNED.md`
  section "Smart App Control" for the four workaround options. Never silently skip
  the boot-gate -- record the SAC state in the commit/PR description.

## What this does NOT replace

- `utility.cmd cameo --check-yaml` is a SEPARATE linting tool (takes 10+ minutes).
  It catches different issues (broken prerequisites, naming). Use it selectively.
- The Python audits (`tools/audit/run_all.sh`). Run those too before committing.
