@echo off
setlocal EnableDelayedExpansion

FOR /F "usebackq tokens=1,2 delims==" %%A IN ("mod.config") DO (set "%%A=%%~B")
if exist user.config (FOR /F "usebackq tokens=1,2 delims==" %%A IN ("user.config") DO (set "%%A=%%~B"))

if "%MOD_ID%"=="" (
    echo Required mod.config variables are missing.
    exit /b 1
)
if "%ENGINE_VERSION%"=="" exit /b 1
if "%ENGINE_DIRECTORY%"=="" exit /b 1

set TEMPLATE_DIR=%CD%

pushd "%ENGINE_DIRECTORY%"
set ENGINE_DIR=%CD%
popd

if not exist "%ENGINE_DIR%\bin\OpenRA.exe" (
    echo Required engine files not found.
    exit /b 1
)

set MOD_SEARCH_PATHS=%TEMPLATE_DIR%\mods,%ENGINE_DIR%\mods

echo Boot test: launching OpenRA for 30s...
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%ENGINE_DIR%\bin\OpenRA.exe' -ArgumentList 'Game.Mod=%MOD_ID%','Engine.EngineDir=..','Engine.LaunchPath=%TEMPLATE_DIR%\boot-test.cmd','Engine.ModSearchPaths=%MOD_SEARCH_PATHS%' -WorkingDirectory '%ENGINE_DIR%' -PassThru; if ($proc.WaitForExit(30000)) { exit $proc.ExitCode }; if (-not $proc.CloseMainWindow()) { $proc.Kill() } elseif (-not $proc.WaitForExit(5000)) { $proc.Kill() }; exit 0"
set "BOOT_EXIT=%ERRORLEVEL%"

echo Boot test complete.
exit /b %BOOT_EXIT%
