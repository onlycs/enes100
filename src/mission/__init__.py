import asyncio
import logging
import time

from flame import Flame
from libml import LibML
from mission.io import Inputs, Outputs, Routine, State, Ultrasonics
from motor import Drivetrain

EVENT_LOOP_MS = 20


def _initial_state(actual: State) -> Routine:
    yield Outputs()
    return actual


class StateMachine:
    log: logging.Logger = logging.getLogger("MissionFLO")

    def __init__(
        self,
        ml: LibML,
        flames: list[Flame],
        us: Ultrasonics,
        dt: Drivetrain,
        initial: State,
    ):
        self.state: Routine = _initial_state(initial)
        self.ml = ml
        self.flames = flames
        self.us = us
        self.dt = dt
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
