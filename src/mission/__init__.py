import time

from flame import Flame
from libml import LibML
from mission.helpers import AsyncStack
from mission.io import Inputs, State
from mission.states import InitialState
from motor import Drivetrain
from ultrasonic import HCSR04


class StateMachine:
    def __init__(
        self, ml: LibML, flames: list[Flame], ultrasonics: list[HCSR04], dt: Drivetrain
    ):
        self.state: State = InitialState.create()
        self.ml = ml
        self.flames = flames
        self.ultrasonics = ultrasonics
        self.dt = dt
        self.last_tick = time.ticks_ms()

    async def tick(self):
        dt = time.ticks_diff(self.last_tick, time.ticks_ms())
        self.last_tick = time.ticks_ms()

        ins = Inputs(self.ml, self.flames, self.ultrasonics, dt)
        outs = await self.state.ontick(ins)
        defer = AsyncStack()

        if outs.transition is not None:
            next = outs.transition()
            defer.append(self.state.onexit(ins), next.onenter(ins))
            self.state = next

        for message in outs.messages:
            defer.append(self.ml.print(message))

        if outs.motors is not None:
            self.dt.set(*outs.motors)

        await defer.join()
