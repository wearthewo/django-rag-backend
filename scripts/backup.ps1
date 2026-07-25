$ErrorActionPreference = "Stop"
$backupDirectory = Join-Path $PSScriptRoot "..\backups"
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupFile = Join-Path $backupDirectory "shopfinder-$timestamp.sql"
docker compose --profile core exec -T db pg_dump -U postgres django_rag | Set-Content -Encoding utf8 -LiteralPath $backupFile
Write-Output "Database backup written to $backupFile"
