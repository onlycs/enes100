# ruff: noqa: UP035
from typing import Callable, Generator, Sequence  # pyright: ignore[reportDeprecated]

from flame import Flame
from libml import LibML
from libml.op import Print
from ultrasonic import HCSR04


class Ultrasonics:
    def __init__(self, front: HCSR04, left: HCSR04, right: HCSR04) -> None:
        self.front = front
        self.left = left
        self.right = right


class UltrasonicReadings:
    def __init__(self, us: Ultrasonics) -> None:
        self.front = us.front.distance_cm
        self.left = us.left.distance_cm
        self.right = us.right.distance_cm


class Inputs:
    def __init__(
        self, ml: LibML, flames: list[Flame], us: Ultrasonics, dt: float
    ) -> None:
        """Reads a snapshots of inputs from devices"""

        self.pose = ml.pose()
        self.flames = [fl.read() for fl in flames]
        self.us = UltrasonicReadings(us)
        self.dt = dt


class Outputs:
    def __init__(
        self,
        *,
        messages: Sequence[Print | str] | None = None,
        motors: tuple[float, float] | None = None,
    ) -> None:
        self.messages = messages if messages is not None else []
        self.motors = motors


State = Callable[[], "Routine"]
Routine = Generator[Outputs, Inputs, State]
