import asyncio
import logging
import time

from flame import Flame
from libml import LibML
from mission.io import Inputs, Outputs, Routine, State
from motor import Drivetrain
from ultrasonic import HCSR04

EVENT_LOOP_MS = 20


class StateMachine:
    log: logging.Logger = logging.getLogger("MissionFLO")

    def __init__(
        self,
        ml: LibML,
        flames: list[Flame],
        ultrasonics: list[HCSR04],
        dt: Drivetrain,
        initial: State,
    ):
        self.state: Routine = initial()
        self.ml = ml
        self.flames = flames
        self.ultrasonics = ultrasonics
        self.dt = dt
        self.last_tick = time.ticks_ms()

    async def tick(self):
        dt = time.ticks_diff(time.ticks_ms(), self.last_tick)
        self.last_tick = time.ticks_ms()

        ins: Inputs = Inputs(self.ml, self.flames, self.ultrasonics, dt)
        outs: Outputs

        try:
            outs = self.state.send(ins)
        except StopIteration as stopped:
            self.state = stopped.value()
            outs = next(self.state)

        if outs.motors is not None:
            self.dt.set(*outs.motors)

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
