import logging
import os
import time

import arrow
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import connection
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer

from routechoices.core.models import Device, TcpDeviceCommand
from routechoices.lib.helpers import random_key
from routechoices.lib.validators import validate_imei

logger = logging.getLogger("TCP Rotating Log")
logger.setLevel(logging.INFO)
logger_filename = "tcp.log"
logger_suffix = os.environ.get("TCP_SERVER_INSTANCE", "")
if logger_suffix:
    logger_filename = f"tcp-{logger_suffix}.log"

handler = logging.handlers.RotatingFileHandler(
    os.path.join(settings.BASE_DIR, "logs", logger_filename),
    maxBytes=50_000_000,
    backupCount=10,
)
formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d, %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


ROLLOVER_CYCLE = 1024 * 7 * 24 * 3600
ROLLOVER_THRESHOLD = ROLLOVER_CYCLE - 90 * 24 * 3600


class GenericTCPServer(TCPServer):
    connection_class = None

    async def handle_stream(self, stream, address):
        if not self.connection_class:
            return
        c = self.connection_class(stream, address, logger)
        try:
            await c.start_listening()
        except StreamClosedError:
            pass


class GenericConnection:
    def __init__(self, stream, address, logger):
        print(f"{self.protocol_name} - New connection from {address}")
        self.aid = random_key()
        self.imei = None
        self.address = address
        self.stream = stream
        self.stream.set_close_callback(self._on_close)
        self.db_device = None
        self.logger = logger

    async def process_identification(self, imei):
        if self.imei:
            if imei != self.imei:
                raise Exception("Cannot change IMEI")
            return
        validate_imei(imei)
        self.db_device = await get_device_by_imei(imei)
        if not self.db_device:
            raise Exception(f"Imei {imei} not registered")
        if not self.db_device.user_agent:
            self.db_device.user_agent = self.protocol_name
        self.imei = imei
        print(f"{self.protocol_name} - {self.imei} is connected")

    def _on_close(self):
        print(f"{self.protocol_name} - Client quit", flush=True)


@sync_to_async
def get_device_by_imei(imei):
    device = Device.objects.filter(physical_device__imei=imei).first()
    connection.close()
    return device


@sync_to_async
def add_locations(device, locations):

    corrected_locations = []
    current_time = time.time()
    for location in locations:
        ts, lat, lon = location
        while current_time - ts > ROLLOVER_THRESHOLD:
            ts += ROLLOVER_CYCLE
        corrected_locations.append((ts, lat, lon))

    device.add_locations(corrected_locations)
    connection.close()


@sync_to_async
def send_sos(device):
    r = device.send_sos()
    connection.close()
    return r


@sync_to_async
def save_device(device):
    device.save()
    connection.close()


@sync_to_async
def get_pending_commands(imei):
    commands = list(
        TcpDeviceCommand.objects.filter(target__imei=imei, sent=False).values_list(
            "command", flat=True
        )
    )
    t = arrow.now().datetime
    connection.close()
    return t, commands


@sync_to_async
def mark_pending_commands_sent(imei, max_date):
    r = TcpDeviceCommand.objects.filter(
        target__imei=imei,
        sent=False,
        creation_date__lte=max_date,
    ).update(sent=True, modification_date=arrow.now().datetime)
    connection.close()
    return r
