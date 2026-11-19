# ruff: noqa: UP035
from typing import Callable, Generator, Sequence  # pyright: ignore[reportDeprecated]

from devices.flame import Flame
from devices.ultrasonic import Ultrasonics
from libml import LibML
from libml.op import Print


class UltrasonicReadings:
    def __init__(self, us: Ultrasonics) -> None:
        self.front_cm = us.front_cm
        self.left_cm = us.left_cm
        self.right_cm = us.right_cm


class Inputs:
    def __init__(
        self, ml: LibML, flames: list[Flame], us: Ultrasonics, dt: int
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
        servo_degrees: float | None = None,
    ) -> None:
        self.messages = messages if messages is not None else []
        self.motors = motors
        self.servo_degrees = servo_degrees


Routine = Generator[Outputs, Inputs, "Routine"]
