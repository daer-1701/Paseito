$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskPidPath = Join-Path $taskRoot 'tmp/presentation/process.json'
if (!(Test-Path -LiteralPath $taskPidPath)) { Write-Output 'No hay un tunel de presentacion registrado.'; exit 0 }
$taskSaved = Get-Content -LiteralPath $taskPidPath -Raw | ConvertFrom-Json
$taskProcess = Get-Process -Id $taskSaved.pid -ErrorAction SilentlyContinue
if ($taskProcess -and $taskProcess.ProcessName -eq 'cloudflared' -and
    $taskProcess.StartTime.ToUniversalTime().Ticks.ToString() -eq $taskSaved.started) {
    Stop-Process -Id $taskProcess.Id
    Write-Output 'Tunel de presentacion detenido. Jarvis y la voz GPU siguen activos en localhost.'
} else { Write-Output 'El proceso registrado ya no esta activo; no se detuvo otro proceso.' }
