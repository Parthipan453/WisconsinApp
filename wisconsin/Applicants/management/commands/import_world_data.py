import json
import urllib.request
import gzip
import io
import tempfile
import os
from django.core.management.base import BaseCommand
from Applicants.models import Country, StateProvince, City

RELEASE_URL = "https://github.com/dr5hn/countries-states-cities-database/releases/latest/download/json-countries+states+cities.json.gz"
BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "Import all countries, states, and cities from the dr5hn world dataset"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="Path to local JSON file (skips download)")

    def handle(self, *args, **options):
        local_file = options.get("file")

        if local_file:
            self.stdout.write(f"Reading from local file: {local_file}")
            with open(local_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            self.stdout.write(f"Downloading dataset from release...")
            req = urllib.request.Request(
                RELEASE_URL,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read()
            self.stdout.write(f"Downloaded {len(raw):,} bytes (gzipped)")
            decompressed = gzip.decompress(raw)
            data = json.loads(decompressed)
            self.stdout.write(self.style.SUCCESS(f"Decompressed to {len(decompressed):,} bytes"))

        self.stdout.write(f"Loaded {len(data)} countries")
        self._import(data)

    def _import(self, data):
        self.stdout.write("Clearing existing data...")
        City.objects.all().delete()
        StateProvince.objects.all().delete()
        Country.objects.all().delete()

        state_objects = []
        city_objects = []
        country_state_map = {}  # country_iso2 -> state_db_id
        total_states = 0
        total_cities = 0

        self.stdout.write("Building country objects...")
        country_objects = []
        seen_codes = set()
        for country in data:
            cc = country.get("iso2", "")
            name = country.get("name", "")
            if cc and name and cc not in seen_codes:
                seen_codes.add(cc)
                country_objects.append(Country(name=name, code=cc))
        Country.objects.bulk_create(country_objects, batch_size=BATCH_SIZE)
        self.stdout.write(f"Imported {len(country_objects):,} countries")

        self.stdout.write("Building state objects...")
        for country in data:
            cc = country.get("iso2", "")
            if not cc:
                continue
            for state in country.get("states", []):
                state_objects.append(
                    StateProvince(
                        name=state["name"],
                        code=state.get("state_code", ""),
                        country_code=cc,
                    )
                )

        self.stdout.write(f"Bulk creating {len(state_objects):,} states...")
        StateProvince.objects.bulk_create(state_objects, batch_size=BATCH_SIZE)
        total_states = len(state_objects)
        state_objects = None

        self.stdout.write("Loading state ID map for city lookup...")
        states_qs = StateProvince.objects.values("id", "name", "country_code")
        state_map = {}
        for s in states_qs:
            key = (s["country_code"], s["name"])
            state_map[key] = s["id"]

        self.stdout.write("Building city objects...")
        city_batch = []
        for country in data:
            cc = country.get("iso2", "")
            if not cc:
                continue
            for state in country.get("states", []):
                state_id = state_map.get((cc, state["name"]))
                if not state_id:
                    continue
                for city in state.get("cities", []):
                    city_batch.append(
                        City(
                            name=city["name"],
                            state_id=state_id,
                            country_code=cc,
                        )
                    )
                    if len(city_batch) >= BATCH_SIZE:
                        City.objects.bulk_create(city_batch, batch_size=BATCH_SIZE)
                        total_cities += len(city_batch)
                        self.stdout.write(f"  {total_cities:,} cities created so far...")
                        city_batch = []

        if city_batch:
            City.objects.bulk_create(city_batch, batch_size=BATCH_SIZE)
            total_cities += len(city_batch)

        country_count = Country.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Done! Imported {country_count:,} countries, {total_states:,} states and {total_cities:,} cities"
        ))
