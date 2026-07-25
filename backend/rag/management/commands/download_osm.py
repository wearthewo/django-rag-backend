from pathlib import Path

import requests
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Download the free Geofabrik Greece OSM PBF extract explicitly."

    def add_arguments(self, parser):
        parser.add_argument("--output", default="data/greece-latest.osm.pbf")
        parser.add_argument(
            "--url", default="https://download.geofabrik.de/europe/greece-latest.osm.pbf"
        )

    def handle(self, *args, **options):
        output = Path(options["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".part")
        try:
            with requests.get(options["url"], stream=True, timeout=(10, 300)) as response:
                response.raise_for_status()
                with temporary.open("wb") as target:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            target.write(chunk)
            temporary.replace(output)
        except requests.RequestException as exc:
            temporary.unlink(missing_ok=True)
            raise CommandError(f"OSM download failed: {exc}") from exc
        self.stdout.write(self.style.SUCCESS(f"Saved {output}"))
