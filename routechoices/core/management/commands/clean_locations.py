import multiprocessing
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

import arrow
from django.core.management.base import BaseCommand
from django.db.models import Prefetch
from django.utils.timezone import now

from routechoices.core.models import Competitor, Device

CPU_COUNT = multiprocessing.cpu_count()


class Command(BaseCommand):
    help = "Remove unused locations older than 14 days from devices"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", default=False)
        parser.add_argument("--since", type=str, required=False)
        parser.add_argument("-w", "--workers", type=int, default=CPU_COUNT)

    def handle_device(self, device, until, force):
        location_count_before = device.location_count
        device.remove_unused_location(until=until, save=force)
        location_count_after = device.location_count
        return location_count_before - location_count_after

    def handle(self, *args, **options):
        force = options["force"]
        since = options.get("since")
        date_since = None
        if since:
            try:
                date_since = arrow.get(since).datetime
            except ValueError:
                self.stderr.write(self.style.ERROR("Invalid since parameter"))
                sys.exit(1)
                return

        deleted_count = 0
        devices = (
            Device.objects.prefetch_related(
                Prefetch(
                    "competitor_set",
                    queryset=Competitor.objects.select_related("event"),
                )
            )
            .filter(virtual=False)
            .exclude(locations_encoded="")
        )
        if date_since:
            devices = devices.filter(modification_date__gte=date_since)
        two_weeks_ago = now() - timedelta(days=14)
        try:
            with ThreadPoolExecutor(max_workers=options.get("workers")) as executor:
                future_to_device = {
                    executor.submit(
                        self.handle_device, device, two_weeks_ago, force
                    ): device
                    for device in devices
                }
                for future in as_completed(future_to_device):
                    device_deleted_count = future.result()
                    if device_deleted_count:
                        deleted_count += device_deleted_count
        except KeyboardInterrupt:
            return
        if deleted_count == 0:
            self.stdout.write(self.style.SUCCESS("No locations to remove"))
        elif force:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully removed {deleted_count} locations")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"{deleted_count} locations could be removed")
            )
