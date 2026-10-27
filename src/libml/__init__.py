import _thread
import asyncio
import logging
import time

from machine import UART

from . import op
from .types import Pose


class Locked:
    def __init__(self, it):
        super().__init__()
        self.it = it
        self.lock: _thread.LockType = _thread.allocate_lock()

    def __enter__(self):
        self.lock.acquire()
        return self.it

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.lock.release()
        return False

    async def __aenter__(self):
        while not self.lock.acquire(0):
            await asyncio.sleep_ms(1)

        return self.it

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.lock.release()
        return False

    def set(self, it):
        with self:
            self.it = it


class LibML:
    connected = op.IsConnected()
    log: logging.Logger = logging.getLogger("LibML")

    def __init__(self, uart: UART, aruco: int, name: str, room: int, model: int):
        self.uart = Locked(uart)
        self._pose: Locked = Locked(None)

        self._begin = op.Begin(aruco, name, room)
        self._predict = op.MLPredict(model)

    async def handshake(self):
        self.log.debug("Starting handshake")

        n = 0
        while True:
            if n == 0:
                self.log.debug("Waiting for connection")

            async with self.uart as uart:
                self.connected.write(uart)
                res = await op.StateResponse.read(uart)

                if res is not None:
                    break

            await asyncio.sleep_ms(50)

            n += 1
            n %= 20

        self.log.info("UART connection success")
        async with self.uart as uart:
            self._begin.write(uart)

        n = 0
        while True:
            if n == 0:
                self.log.debug("Waiting for WiFi")

            async with self.uart as uart:
                self.connected.write(uart)
                res = await op.StateResponse.read(uart)

                if res == op.StateResponse.CONNECTED:
                    break

            await asyncio.sleep_ms(50)

            n += 1
            n %= 20

        self.log.info("WiFi connection success")
        _thread.start_new_thread(self._pose_thread, ())

    def _pose_thread(self):
        self.log.debug("Starting pose thread")

        check = op.Check()
        pose = None

        while True:
            with self.uart as uart:
                check.write(uart)
                status = op.PoseStatus.read_blocking(uart)

                if status == op.PoseStatus.LOST:
                    pose = None
                elif status == op.PoseStatus.FOUND:
                    pose = op.PoseFound.read_blocking(uart)

            self._pose.set(pose)
            time.sleep_ms(10)

    async def report(self, message: op.MissionMessage):
        async with self.uart as uart:
            message.write(uart)

    def pose(self) -> Pose | None:
        with self._pose as pose:
            return pose

    async def print(self, message: str) -> None:
        async with self.uart as uart:
            op.Print(message).write(uart)

    async def predict(self) -> int | None:
        async with self.uart as uart:
            self._predict.write(uart)
            return await op.MLPrediction.read(uart)
