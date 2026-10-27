import asyncio
import time

from machine import UART

from .types import Pose

FLUSH = b"\xff\xfe\xfd\xfc"
MISSION_FIRE = 0x03


async def read(uart: UART, n: int, timeout_ms: int) -> bytes | None:
    data = b""
    start = time.ticks_ms()

    while len(data) < n:
        k = uart.any()
        if k:
            data += uart.read(min(k, n - len(data)))  # pyright: ignore[reportOperatorIssue]
            continue

        if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
            return None

        await asyncio.sleep_ms(1)

    return data


def read_blocking(uart: UART, n: int, timeout_ms: int) -> bytes | None:
    data = b""
    start = time.ticks_ms()

    while len(data) < n:
        k = uart.any()
        if k:
            data += uart.read(min(k, n - len(data)))  # pyright: ignore[reportOperatorIssue]
            continue

        if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
            return None

        time.sleep_ms(1)

    return data


def s16(lo: int, hi: int) -> int:
    v = lo | (hi << 8)
    return v - 0x10000 if v >= 0x8000 else v


def drain(uart: UART):
    while uart.any():
        uart.read()


class Response:
    TIMEOUT: int
    BYTES: int

    @staticmethod
    def _parse(data: bytes | None):
        raise NotImplementedError()

    @classmethod
    def read_blocking(cls, uart: UART):
        return cls._parse(read_blocking(uart, cls.BYTES, cls.TIMEOUT))

    @classmethod
    async def read(cls, uart: UART):
        return cls._parse(await read(uart, cls.BYTES, cls.TIMEOUT))


class IsConnected:
    OPCODE = 0x07

    def write(self, uart: UART):
        drain(uart)
        uart.write(bytes([self.OPCODE]))


class StateResponse(Response):
    TIMEOUT = 100
    BYTES = 1

    AWAIT_BEGIN = 0x00
    CONNECTED = 0x01

    @staticmethod
    def _parse(data: bytes | None) -> int | None:
        if data is None or data[0] not in (0x00, 0x01):
            return None

        return data[0]


class Begin:
    OPCODE = 0x01

    def __init__(self, aruco_id: int, team_name: str, room_no: int):
        self.aruco_id = aruco_id
        self.team_name = team_name
        self.room_no = room_no

    def write(self, uart: UART):
        drain(uart)
        uart.write(bytes([self.OPCODE, MISSION_FIRE]))
        uart.write(self.aruco_id.to_bytes(2, "big"))
        uart.write(self.room_no.to_bytes(2, "big"))
        uart.write(f"{self.team_name}\0".encode())
        uart.write(FLUSH)


class Check:
    OPCODE = 0x03

    def write(self, uart: UART):
        drain(uart)
        uart.write(bytes([self.OPCODE]))


class PoseStatus(Response):
    TIMEOUT = 10
    BYTES = 1

    CACHE = 0x00
    LOST = 0x01
    FOUND = 0x02

    @staticmethod
    def _parse(data: bytes | None) -> int | None:
        if data is None:
            return None

        return data[0]


class PoseFound(Response):
    TIMEOUT = 30
    BYTES = 5

    @staticmethod
    def _parse(data: bytes | None) -> Pose | None:
        if data is None:
            return

        y = data[0] / 100
        x = (data[1] | (data[2] << 8)) / 100
        t = s16(data[3], data[4]) / 100

        return Pose(x, y, t)


class MissionMessage:
    OP: int = 0x02

    def fmt(self) -> str:
        raise NotImplementedError()

    def write(self, uart: UART):
        drain(uart)
        uart.write(bytes([MissionMessage.OP]))
        uart.write(f"MISSION MESSAGE: {self.fmt()}\n\0".encode())
        uart.write(FLUSH)


class MissionCandles(MissionMessage):
    def __init__(self, num: int):
        super().__init__()
        self.num = max(min(num, 4), 0)

    def fmt(self) -> str:
        return f"The number of candles lit is {self.num}."


class MissionFacing(MissionMessage):
    def __init__(self, facing: str):
        super().__init__()

        if facing not in ["A", "B", "C"]:
            facing = "A"

        self.facing = facing

    def fmt(self) -> str:
        return f"The topography of the fire mission is:  {self.facing}"


class Print:
    OPCODE = 0x02

    def __init__(self, msg: str) -> None:
        self.msg = msg

    def write(self, uart: UART):
        uart.write(bytes([Print.OPCODE]))
        uart.write(f"{self.msg}\n\0".encode())
        uart.write(FLUSH)


class MLPredict:
    OPCODE = 0x05

    def __init__(self, model: int):
        self.model = model

    def write(self, uart: UART):
        drain(uart)
        uart.write(bytes([MLPredict.OPCODE]))
        uart.write(self.model.to_bytes(1, "big"))
        uart.write(FLUSH)


class MLPrediction(Response):
    TIMEOUT = 500
    BYTES = 2

    @staticmethod
    def _parse(data: bytes | None) -> int | None:
        if data is None:
            return

        return s16(data[0], data[1])
