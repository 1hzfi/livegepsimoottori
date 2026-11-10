import sys
import urllib.parse

from django.core.management.base import BaseCommand

from routechoices.lib.other_gps_services.livelox import Livelox


class Command(BaseCommand):
    help = "Download Livelox event KMZ file"

    def add_arguments(self, parser):
        parser.add_argument("-u", "--url", dest="event_url", type=str)
        parser.add_argument("-o", "--output", dest="output", type=str)

    def handle(self, *args, **options):
        event_url = options["event_url"]
        prefix = "https://www.livelox.com/Viewer/"
        if event_url.startswith(prefix):
            event_url = urllib.parse.urlparse(event_url).query
        livelox = Livelox()
        try:
            livelox.parse_init_data(event_url)
            event = livelox.get_or_create_event()
            livelox.assign_maps_to_event(event)
        except ValueError:
            self.stderr.write(self.style.ERROR("Could not fetch Livelox event data…"))
            sys.exit(1)
            return
        with open(options["output"], "wb") as fp:
            fp.write(event.map.kmz)
        self.stdout.write(self.style.SUCCESS("KMZ downloaded succesfully."))
