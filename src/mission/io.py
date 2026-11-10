# ruff: noqa: UP035
from typing import Callable, Generator  # pyright: ignore[reportDeprecated]

from flame import Flame
from libml import LibML
from libml.op import Print
from ultrasonic import HCSR04


class Inputs:
    def __init__(
        self, ml: LibML, flames: list[Flame], ultrasonics: list[HCSR04], dt: float
    ) -> None:
        """Reads a snapshots of inputs from devices"""

        self.pose = ml.pose()
        self.flames = [fl.read() for fl in flames]
        self.ultrasonics = [us.distance_cm for us in ultrasonics]
        self.dt = dt


class Outputs:
    def __init__(
        self,
        *,
        messages: list[Print | str] | None = None,
        motors: tuple[float, float] | None = None,
    ) -> None:
        self.messages = messages if messages is not None else []
        self.motors = motors


State = Callable[[], "Routine"]
Routine = Generator[Outputs, Inputs, State]
