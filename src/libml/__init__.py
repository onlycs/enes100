import _thread
import asyncio
import time
from typing import Generic, TypeVar

from machine import UART

from . import op
from .types import Pose

T = TypeVar("T")


class Locked(Generic[T]):
    def __init__(self, it: T):
        super().__init__()
        self.it = it
        self.lock: _thread.LockType = _thread.allocate_lock()

    def __enter__(self) -> T:
        self.lock.acquire()
        return self.it

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.lock.release()
        return False

    async def __aenter__(self) -> T:
        while not self.lock.acquire(0):
            await asyncio.sleep_ms(1)

        return self.it

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.lock.release()
        return False

    def set(self, it: T):
        with self:
            self.it = it


class LibML:
    connected = op.IsConnected()

    def __init__(self, uart: UART, aruco: int, name: str, room: int, model: int):
        self.uart = Locked(uart)
        self._pose: Locked[Pose | None] = Locked(None)

        self._begin = op.Begin(aruco, name, room)
        self._predict = op.MLPredict(model)

    async def handshake(self):
        while True:
            async with self.uart as uart:
                self.connected.write(uart)
                res = await op.StateResponse.read(uart)

                if res is not None:
                    break

            await asyncio.sleep_ms(50)

        async with self.uart as uart:
            self._begin.write(uart)

        while True:
            async with self.uart as uart:
                self.connected.write(uart)
                res = await op.StateResponse.read(uart)

                if res == op.StateResponse.CONNECTED:
                    break

            await asyncio.sleep_ms(50)

        _thread.start_new_thread(self._pose_thread, ())

    def _pose_thread(self):
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

    async def predict(self) -> int | None:
        async with self.uart as uart:
            self._predict.write(uart)
            return await op.MLPrediction.read(uart)
