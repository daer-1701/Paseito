param(
    [ValidatePattern('^[a-f0-9-]{36}$')]
    [string]$TunnelId = 'dd97dbcb-3c29-4306-a748-d51f23f68679',
    [ValidatePattern('^[a-z0-9][a-z0-9.-]+[a-z0-9]$')]
    [string]$Hostname = 'jarvis.timosboy.win',
    [ValidateRange(1024,65535)]
    [int]$Port = 8082
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskFolder = Join-Path $taskRoot 'tmp/presentation'
$taskCredentials = Join-Path ([Environment]::GetFolderPath('UserProfile')) ".cloudflared/$TunnelId.json"
if (!(Test-Path -LiteralPath $taskCredentials)) { throw 'Faltan las credenciales locales del tunel. Ejecuta cloudflared login y configura un tunel propio.' }
$taskExecutable = (Get-Command cloudflared -ErrorAction Stop).Source
Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing | Out-Null
New-Item -ItemType Directory -Path $taskFolder -Force | Out-Null
$taskPidPath = Join-Path $taskFolder 'process.json'
if (Test-Path -LiteralPath $taskPidPath) {
    $taskSaved = Get-Content -LiteralPath $taskPidPath -Raw | ConvertFrom-Json
    $taskExisting = Get-Process -Id $taskSaved.pid -ErrorAction SilentlyContinue
    if ($taskExisting -and $taskExisting.ProcessName -eq 'cloudflared' -and
        $taskExisting.StartTime.ToUniversalTime().Ticks.ToString() -eq $taskSaved.started) {
        Write-Output 'El tunel de presentacion ya esta iniciado.'
        exit 0
    }
}
$taskConfig = Join-Path $taskFolder 'cloudflared.yml'
$taskCredentialYaml = $taskCredentials.Replace('\','/')
@"
tunnel: $TunnelId
credentials-file: "$taskCredentialYaml"
ingress:
  - hostname: $Hostname
    service: http://127.0.0.1:$Port
  - service: http_status:404
"@ | Set-Content -LiteralPath $taskConfig -Encoding UTF8
& $taskExecutable tunnel --config $taskConfig ingress validate
if ($LASTEXITCODE -ne 0) { throw 'Configuracion de tunel invalida.' }
$taskProcess = Start-Process -FilePath $taskExecutable -ArgumentList @('tunnel','--config',('"'+$taskConfig+'"'),'--protocol','http2','run',$TunnelId) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskFolder 'stdout.log') -RedirectStandardError (Join-Path $taskFolder 'stderr.log')
@{pid=$taskProcess.Id;started=$taskProcess.StartTime.ToUniversalTime().Ticks.ToString()} | ConvertTo-Json | Set-Content -LiteralPath $taskPidPath -Encoding UTF8
Write-Output "Tunel iniciado. URL: https://$Hostname. Logs locales: tmp/presentation."
