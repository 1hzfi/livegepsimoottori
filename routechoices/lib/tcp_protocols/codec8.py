from io import BytesIO
from struct import pack, unpack

from tornado.iostream import StreamClosedError

from routechoices.lib.helpers import safe64encode
from routechoices.lib.tcp_protocols.commons import (
    GenericConnection,
    GenericTCPServer,
    add_locations,
    send_sos,
)


def read_ext_bytes(buffer, codec, codecs):
    if codec in codecs:
        return unpack(">H", buffer.read(2))[0]
    return buffer.read(1)[0]


class TMT250Decoder:
    def __init__(self):
        self.packet = {}
        self.battery_level = None
        self.alarm_triggered = False
        self.extended = False

    def generate_response(self, success=True):
        s = self.packet["num_data"] if success else 0
        return pack(">i", s)

    def decode_alv(self, data):
        self.packet["zeroes"] = unpack(">i", data[:4])[0]
        if self.packet["zeroes"] != 0:
            raise ValueError("zeroes should be 0")

        self.packet["length"] = unpack(">i", data[4:8])[0]

        self.packet["codec"] = data[8]

        if self.packet["codec"] not in (0x08, 0x8E):
            raise ValueError("codec should be 0x08 or 0x8E")

        if self.packet["codec"] == 0x8E:
            self.extended = True

        self.packet["num_data"] = data[9]
        buffer = BytesIO(data[10:])
        self.packet["records"] = []
        for _ in range(self.packet["num_data"]):
            self.extract_records(buffer)
        return self.packet

    def extract_records(self, buffer):
        self.alarm_triggered = False
        global_mask = 0x0F
        timestamp = unpack(">Q", buffer.read(8))[0] / 1e3
        buffer.read(1)  # priority
        lon = unpack(">i", buffer.read(4))[0] / 1e7
        lat = unpack(">i", buffer.read(4))[0] / 1e7
        buffer.read(2)  # alt
        buffer.read(2)  # angle
        buffer.read(1)  # satellites
        buffer.read(2)  # speed
        read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
        read_ext_bytes(buffer, self.packet["codec"], (0x8E,))  # total io data
        read_data = 0
        if global_mask & 0x01:
            cnt = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
            for _ in range(cnt):
                avl_id = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
                if avl_id == 113:
                    self.battery_level = buffer.read(1)[0]
                elif avl_id == 236:
                    self.alarm_triggered = buffer.read(1)[0] > 0
                else:
                    buffer.read(1)
                read_data += 1
        if global_mask & 0x02:
            cnt = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
            for _ in range(cnt):
                avl_id = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
                buffer.read(2)
                read_data += 1
        if global_mask & 0x04:
            cnt = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
            for _ in range(cnt):
                avl_id = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
                buffer.read(4)
                read_data += 1

        cnt = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
        for _ in range(cnt):
            avl_id = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
            buffer.read(8)
            read_data += 1

        if self.extended:
            cnt = read_ext_bytes(buffer, self.packet["codec"], (0x8E,))
            for _ in range(cnt):
                avl_id = unpack(">H", buffer.read(2))[0]
                length = unpack(">H", buffer.read(2))[0]
                buffer.read(length)
                read_data += 1

        self.packet["records"].append(
            {
                "timestamp": timestamp,
                "latlon": [lat, lon],
            }
        )


class Codec8Connection(GenericConnection):
    protocol_name = "Codec8"

    def __init__(self, stream, address, logger):
        super().__init__(stream, address, logger)
        self.buffer = None
        self.packet_len = 0
        self.decoder = TMT250Decoder()

    async def parse_imei(self, data):
        imei_len = (data[0] << 8) + data[1]
        imei = ""
        try:
            imei = data[2:17].decode("ascii")
            if imei_len != len(imei):
                raise Exception("Invalid IMEI length")
            await self.process_identification(imei)
        except Exception:
            await self.stream.write(b"\x00")
            self.stream.close()
            print(
                f"Codec8 - invalid identification {self.address}, {imei}, {imei_len}",
                flush=True,
            )
        else:
            await self.stream.write(b"\x01")
            self.logger.info(
                f"CODEC8 CONN, {self.aid}, {self.address}, {self.imei}: {safe64encode(bytes(data))}"
            )

    async def start_listening(self):
        print("Codec8 - Listening from", self.address)

        while True:
            try:
                data = bytearray(b"\x00" * 2048)
                data_len = await self.stream.read_into(data, partial=True)
                data = data[:data_len]
                if self.imei:
                    self.logger.info(
                        f"CODEC8 DATA, {self.aid}, {self.address}, {self.imei}: "
                        f"{safe64encode(bytes(data))}"
                    )

                if data_len == 1 and data[0] == b"\xff":
                    print("Codec8 - heartbeat", flush=True)
                elif data_len > 2:
                    imei_len = (data[0] << 8) + data[1]
                    if imei_len > 0:
                        await self.parse_imei(data[:17])
                    elif self.imei:
                        await self.decode_data(data)
                    else:
                        self.stream.close()
                        break
            except StreamClosedError:
                break

    async def decode_data(self, data):
        if not self.imei:
            pass
        zeroes = unpack(">i", data[:4])[0]
        if zeroes != 0:
            return
        self.packet_length = unpack(">i", data[4:8])[0] + 4
        self.buffer = bytes(data)
        await self._on_full_data()

    async def _on_full_data(self):
        try:
            decoded = self.decoder.decode_alv(self.buffer)
        except Exception:
            print("Codec8 - error decoding packet")
            await self.stream.write(self.decoder.generate_response(False))
        else:
            loc_array = []
            for r in decoded.get("records", []):
                loc_array.append((int(r["timestamp"]), r["latlon"][0], r["latlon"][1]))
            if not self.db_device.user_agent:
                self.db_device.user_agent = self.protocol_name
            if self.decoder.battery_level:
                self.db_device.battery_level = self.decoder.battery_level
            await add_locations(self.db_device, loc_array)
            print(
                f"Codec8 - {self.imei} wrote {len(loc_array)} locations to DB",
                flush=True,
            )
            self.waiting_for_content = True
            if self.decoder.alarm_triggered:
                sos_device_aid, sos_lat, sos_lon, sos_sent_to = await send_sos(
                    self.db_device
                )
                print(
                    f"Codec8 - SOS triggered by device {sos_device_aid}, {sos_lat}, {sos_lon}"
                    f" email sent to {sos_sent_to}",
                    flush=True,
                )
            await self.stream.write(self.decoder.generate_response())


class TCPServer(GenericTCPServer):
    connection_class = Codec8Connection
