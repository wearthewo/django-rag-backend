$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}
docker compose --profile core build
docker compose --profile core up -d
docker compose --profile core exec web python manage.py migrate
docker compose --profile core exec web python manage.py seed_demo_shops
Write-Output "Agora Scout is ready at http://localhost:5173"
