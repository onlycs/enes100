# ruff: noqa: UP035

import asyncio
import logging
import time
from typing import Callable

from devices.flame import Flame
from devices.motor import Drivetrain
from devices.servo import DS3218
from devices.ultrasonic import Ultrasonics
from libml import LibML
from mission.io import Inputs, Outputs, Routine
from mission.states import to_mission_site

EVENT_LOOP_MS = 20


def _initial_state(actual: Callable[[], Routine]) -> Routine:
    yield Outputs()
    return actual()


class StateMachine:
    log: logging.Logger = logging.getLogger("MissionFLO")

    def __init__(
        self,
        ml: LibML,
        flames: list[Flame],
        us: Ultrasonics,
        drive: Drivetrain,
        servo: DS3218,
    ):
        self.state = _initial_state(to_mission_site)
        self.ml = ml
        self.flames = flames
        self.us = us
        self.drive = drive
        self.servo = servo
        self.last_tick = time.ticks_ms()

        next(self.state)

    async def tick(self):
        dt = time.ticks_diff(time.ticks_ms(), self.last_tick)
        self.last_tick = time.ticks_ms()

        ins: Inputs = Inputs(self.ml, self.flames, self.us, dt)
        outs: Outputs

        try:
            outs = self.state.send(ins)
        except StopIteration as stopped:
            self.state = stopped.value()
            outs = next(self.state)

        if outs.motors is not None:
            self.drive.set(*outs.motors)

        if outs.servo_degrees is not None:
            self.servo.write_angle(outs.servo_degrees)

        await asyncio.gather(*[self.ml.print(message) for message in outs.messages])

    async def begin(self):
        while True:
            await self.tick()

            sch = time.ticks_add(self.last_tick, EVENT_LOOP_MS)
            rem = time.ticks_diff(sch, time.ticks_ms())
            if rem < 0:
                self.log.warning(
                    f"Tick loop overrun. Elapsed {EVENT_LOOP_MS - rem} > {EVENT_LOOP_MS}ms. Please use `yield` in your for loops."
                )
                continue

            await asyncio.sleep_ms(rem)
