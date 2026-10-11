# Crea la tarea programada de Windows: corre al iniciar sesión y todos los días a las 9:00.
# Si la compu estaba apagada a esa hora, corre en cuanto se pueda (StartWhenAvailable).
$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $PSScriptRoot
$python = Join-Path $raiz ".venv\Scripts\pythonw.exe"   # pythonw = sin ventana negra
if (-not (Test-Path $python)) { throw "No encuentro .venv. Sigue primero los pasos de instalación del README." }

$accion = New-ScheduledTaskAction -Execute $python -Argument "`"$raiz\recordatorio.py`"" -WorkingDirectory $raiz
$disparadores = @(
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),
    (New-ScheduledTaskTrigger -Daily -At 9:00AM)
)
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName "RecordatorioEntregas" -Action $accion -Trigger $disparadores `
    -Settings $ajustes -Description "Avisa cuando una orden de compra esta por vencer" -Force | Out-Null
Write-Host "Listo. La tarea 'RecordatorioEntregas' quedo instalada." -ForegroundColor Green
