from typing import override

from mission.io import Inputs, Outputs, State


class InitialState(State):
    @override
    async def ontick(self, inputs: Inputs) -> Outputs:
        return Outputs(transition=NavigateToMission)


class NavigateToMission(State):
    @override
    async def ontick(self, inputs: Inputs) -> Outputs:
        return Outputs()
