param([Parameter(Mandatory = $true)][string]$BackupFile)
$ErrorActionPreference = "Stop"
$resolvedBackup = Resolve-Path -LiteralPath $BackupFile
Get-Content -Raw -LiteralPath $resolvedBackup | docker compose --profile core exec -T db psql -U postgres django_rag
Write-Output "Database restored from $resolvedBackup"
