import operator
import re
from functools import reduce
from io import BytesIO
from struct import pack, unpack

import arrow

from routechoices.lib import luhn
from routechoices.lib.tcp_protocols.commons import (
    GenericConnection,
    GenericTCPServer,
    add_locations,
    save_device,
)


def convert_coordinate(raw):
    degrees = raw / 1000000
    minutes = (raw % 1000000) / 10000.0
    return degrees + minutes / 60


def read_bcd_integer(stream, digits):
    offset = 0
    result = 0
    while offset < digits // 2:
        b = stream.read(1)[0]
        result *= 10
        result += b >> 4
        result *= 10
        result += b & 0x0F
        offset += 1
    if digits % 2 != 0:
        b = stream.read(1)[0]
        result *= 10
        result += b >> 4
    return result


def read_slice(stream, length):
    pos = stream.tell()
    full_view = stream.getbuffer()
    slice_view = full_view[pos : pos + length]
    stream.seek(pos + length)
    return slice_view


class JT808Connection(GenericConnection):
    protocol_name = "JT808"

    def __init__(self, stream, address, logger):
        super().__init__(stream, address, logger)
        self.protocol_version = None
        self.delimiter = b"~"
        self.timezone = "+08:00"

    async def decode(self, data):
        buf = BytesIO(data)
        self.delimiter = buf.read(1)
        if self.delimiter == b"(":
            sentence = data.decode()
            if "BASE,2" in sentence:
                response = sentence.replace(
                    "TIME", arrow.get().format("YYYYMMDDHHmmss")
                )
                await self.stream.write(response.encode())
                return
            # Then it was a result, no positions, we skip
            return

        data_type = unpack(">H", buf.read(2))[0]
        attribute = unpack(">H", buf.read(2))[0]
        body_len = attribute & 0x3FF
        has_protocol_version = attribute & 0x4000
        self.protocol_version = buf.read(1)[0] if has_protocol_version else None
        dev_id = read_slice(
            buf, 10 if has_protocol_version else 7 if self.delimiter == 0xE7 else 6
        )

        if data_type in (0x5501, 0x5502):
            index = buf.read(1)[0]
        else:
            index = unpack(">H", buf.read(2))[0]

        imei = self.decode_id(dev_id)
        imei = f"{imei:0>15}"
        try:
            await self.process_identification(imei)
        except Exception as e:
            print(f"{self.protocol_name} - Could not identify device ({e})", flush=True)
            self.stream.close()
            return

        if data_type == 0x0100:  # MSG_TERMINAL_REGISTER
            response = BytesIO()
            response.write(pack(">H", index))
            response.write(b"\x00")
            response.write(self.decode_id(dev_id).encode())
            await self.stream.write(
                self.format_message(0x8100, dev_id, False, response.getvalue())
            )
        elif data_type == 0x0002:  # MSG_HEARTBEAT
            await self.send_general_response(dev_id, data_type, index)
            if buf.getbuffer().nbytes - buf.tell() >= 4:
                battery_level = buf.read(1)[0]
                self.db_device.battery_level = battery_level
                await save_device(self.db_device)
        elif data_type in (0x6006, 0x0102, 0x0506, 0x8888, 0x0003, 0x1007, 0x0107):
            await self.send_general_response(dev_id, data_type, index)
        elif data_type == 0x0200:
            await self.send_general_response(dev_id, data_type, index)
            await self.decode_location(buf)
        elif data_type == 0x0201:
            buf.read(2)
            await self.decode_location(buf)
        elif data_type in (0x5501, 0x5502):
            if attribute & 0x8000:
                await self.send_general_response2(dev_id, data_type)
            await self.decode_location2(buf, data_type)
        elif data_type == 0x0210 and body_len == 7:
            await self.send_general_response(dev_id, data_type, index)
            battery_level = buf.read(1)[0]
            self.db_device.battery_level = battery_level
            await save_device(self.db_device)
        elif data_type in (0x0704, 0x0210):
            await self.send_general_response(dev_id, data_type, index)
            await self.decode_location_batch(buf, data_type)
        elif data_type == 0x0109:
            now = arrow.get().datetime
            response = BytesIO()
            response.write(pack(">H", now.year))
            response.write(pack("B", now.month))
            response.write(pack("B", now.day))
            response.write(pack("B", now.hour))
            response.write(pack("B", now.minute))
            response.write(pack("B", now.second))
            await self.stream.write(
                self.format_message(
                    0x8109,
                    dev_id,
                    False,
                    response.getvalue(),
                )
            )
        elif data_type == 0x0900:
            await self.send_general_response(dev_id, data_type, index)

    def read_coordinates(self, buf):
        status = unpack(">i", buf.read(4))[0]
        is_valid = (status & 0b10) != 0
        lat = unpack(">I", buf.read(4))[0] / 1_000_000
        lng = unpack(">I", buf.read(4))[0] / 1_000_000
        if status & 0b100:
            lat *= -1
        if status & 0b1000:
            lng *= -1
        return is_valid, lat, lng

    def read_date(self, buf, timezone="UTC"):
        year = read_bcd_integer(buf, 2)
        month = read_bcd_integer(buf, 2) + 1
        day = read_bcd_integer(buf, 2)
        hour = read_bcd_integer(buf, 2)
        minute = read_bcd_integer(buf, 2)
        second = read_bcd_integer(buf, 2)
        return arrow.get(
            f"20{year:0>2}-{month:0>2}-{day:0>2}T{hour:0>2}:{minute:0>2}:{second:0>2}",
            tzinfo=self.timezone,
        ).timestamp()

    async def decode_transparent(self, buf):
        locs = []
        data_type = buf.read(1)[0]
        if data_type == 0xF0:
            ts = self.read_date(buf, self.timezone)
            buf.read(2)
            count = None
            sub_type = buf.read(1)[0]
            if sub_type == 0x01:
                count = buf.read(1)[0]
                for i in range(count):
                    buf.read(2)
                    x_len = buf.read(1)[0]
                    buf.read(x_len)
                is_valid, lat, lng = self.read_coordinates(buf)
                if is_valid:
                    locs.append((ts, lat, lng))
            elif sub_type == 0x02:
                count = unpack(">H", buf.read(2))[0]
                for i in range(count):
                    buf.read(4)
                    code_count = unpack(">H", buf.read(2))[0]
                    for j in range(code_count):
                        buf.read(8)
                        x_len = unpack(">H", buf.read(2))[0]
                        buf.read(x_len)
                is_valid, lat, lng = self.read_coordinates(buf)
                if is_valid:
                    locs.append((ts, lat, lng))
            elif sub_type == 0x03:
                count = unpack(">H", buf.read(2))[0]
                for i in range(count):
                    buf.read(1)
                    x_len = buf.read(1)[0]
                    buf.read(x_len)
                is_valid, lat, lng = self.read_coordinates(buf)
                if is_valid:
                    locs.append((ts, lat, lng))
        elif data_type == 0xFF:
            ts = self.read_date(buf, self.timezone)
            lat = unpack(">i", buf.read(4))[0] / 1_000_000
            lng = unpack(">i", buf.read(4))[0] / 1_000_000
            locs.append((ts, lat, lng))
        elif data_type in (0x53, 0x54):
            is_valid, lat, lng = self.read_coordinates(buf)
            buf.read(6)
            ts = self.read_date(buf, self.timezone)
            if is_valid:
                locs.append((ts, lat, lng))
        if locs:
            await add_locations(self.db_device, locs)

    async def decode_location(self, buf, write=True):
        buf.read(4)  # alarm, skip for now
        is_valid, lat, lng = self.read_coordinates(buf)
        buf.read(2)  # altitude data
        buf.read(2)  # speed data
        buf.read(2)  # course data
        ts = self.read_date(buf, self.timezone)

        if buf.getbuffer().nbytes - buf.tell() == 20:
            buf.read(8)
            self.db_device.battery_level = unpack(">H", buf.read(2))[0] / 10
        # There is more data but it is useless for us
        if is_valid:
            if write:
                await add_locations(self.db_device, [(ts, lat, lng)])
            else:
                return (ts, lat, lng)
        return None

    async def decode_location2(self, buf, data_type):
        ts = self.read_date(buf)
        lat = convert_coordinate(read_bcd_integer(buf, 8))
        lng = convert_coordinate(read_bcd_integer(buf, 9))
        flags = buf.read(1)[0]
        is_valid = flags & 0b1
        if flags & 0b10:
            lat *= -1
        if flags & 0b100:
            lng *= -1
        buf.read(9)
        bat = buf.read(1)[0]
        if bat <= 100:
            self.db_device.battery_level = bat

        # There is more data but it is useless for us
        if is_valid and data_type != 0x5502:
            await add_locations(self.db_device, [(ts, lat, lng)])

    async def decode_location_batch(self, buf, data_type):
        locs = []
        if data_type == 0x0704:
            buf.read(3)
        while buf.getbuffer().nbytes - buf.tell() > 2:
            x_len = (
                buf.read(1)[0] if data_type == 0x0210 else unpack(">H", buf.read(2))[0]
            )
            loc_data = read_slice(buf, x_len)
            loc = await self.decode_location(BytesIO(loc_data), write=False)
            if loc:
                locs.append(loc)
        if locs:
            await add_locations(self.db_device, locs)

    def format_message(self, data_type, dev_id, short_index, data):
        buf = BytesIO()
        buf.write(self.delimiter)
        buf.write(pack(">H", data_type))
        attribute = len(data)
        if self.protocol_version is not None:
            attribute |= 0x4000
        buf.write(pack(">H", attribute))
        if self.protocol_version is not None:
            buf.write(pack(">B", self.protocol_version))
        buf.write(dev_id)
        if short_index:
            buf.write(b"\x01")
        else:
            buf.write(b"\x00")
        buf.write(data)
        buf.write(pack("B", reduce(operator.xor, buf.getvalue()[1:])))
        buf.write(self.delimiter)
        return buf.getvalue()

    async def send_general_response(self, dev_id, data_type, index):
        response = BytesIO()
        response.write(pack(">H", index))
        response.write(pack(">H", data_type))
        response.write(b"\x00")
        await self.stream.write(
            self.format_message(
                0x8001,
                dev_id,
                False,
                response.getvalue(),
            )
        )

    async def send_general_response2(self, dev_id, data_type):
        response = BytesIO()
        response.write(pack(">H", data_type))
        response.write(b"\x00")
        await self.stream.write(
            self.format_message(
                0x4401,
                dev_id,
                True,
                response.getvalue(),
            )
        )

    def decode_id(self, dev_id):
        serial = dev_id.hex()
        if re.search(r"[^0-9]", serial):
            imei = unpack(">H", dev_id[0:2])[0] << 32 + unpack(">I", dev_id[2:6])[0]
            imei = luhn.append(f"{imei:0>14}")
            return imei
        serial = serial.lstrip("0")
        return luhn.append(f"{serial:0<14}")

    async def start_listening(self):
        print(f"JT808 - Listening from {self.address}")
        while True:
            data = bytearray(b"\x00" * 2048)
            try:
                bytes_read = await self.stream.read_into(data, partial=True)
            except Exception:
                print(f"{self.protocol_name} - Could not read stream")
                self.stream.close()
                return

            data_read = data[:bytes_read]

            try:
                await self.decode(data_read)
            except Exception as e:
                print(
                    f"{self.protocol_name} - Could not parse location ({e})", flush=True
                )
                self.stream.close()
                return


class TCPServer(GenericTCPServer):
    connection_class = JT808Connection
