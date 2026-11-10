from flame import Flame
from libml import LibML
from libml.op import Print
from ultrasonic import HCSR04


class Inputs:
    def __init__(
        self, ml: LibML, flames: list[Flame], ultrasonics: list[HCSR04]
    ) -> None:
        self.pose = ml.pose()
        self.flames = [fl.read() for fl in flames]
        self.ultrasonics = [us.distance_cm for us in ultrasonics]


class Outputs:
    def __init__(
        self,
        *,
        messages: list[Print] | None = None,
        motors: tuple[float, float] | None = None,
        transition: type["State"] | None = None,
    ) -> None:
        self.messages = messages if messages is not None else []
        self.motors = motors
        self.transition = transition


class State:
    @classmethod
    def create(cls):
        return cls()

    async def onenter(self, _inputs: Inputs) -> Outputs:
        return Outputs()

    async def ontick(self, _inputs: Inputs) -> Outputs:
        return Outputs()

    async def onexit(self, _inputs: Inputs) -> None:
        pass
