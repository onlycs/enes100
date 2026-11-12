from math import atan2, cos, degrees, pi, radians, sin, tau
from typing import override

from PID import PID
from ulab import numpy as np


class Transform2d:
    ZERO: "Transform2d"
    ONE: "Transform2d"
    UNIT_X: "Transform2d"
    UNIT_Y: "Transform2d"

    def __init__(self, position: np.ndarray | tuple[float, float]) -> None:
        if isinstance(position, np.ndarray):
            self.t = position
        else:
            self.t = np.array(position)

    def __add__(self, other: "Transform2d") -> "Transform2d":
        return Transform2d(self.t + other.t)

    def __neg__(self) -> "Transform2d":
        return Transform2d(-self.t)

    def __sub__(self, other: "Transform2d") -> "Transform2d":
        return self + -other

    def __mul__(self, other: "float | Transform2d") -> "Transform2d":
        return (
            Transform2d(self.t * other.t)
            if isinstance(other, Transform2d)
            else Transform2d(self.t * other)
        )

    def __truediv__(self, other: "float | Transform2d") -> "Transform2d":
        return (
            Transform2d(self.t / other.t)
            if isinstance(other, Transform2d)
            else Transform2d(self.t / other)
        )

    @staticmethod
    def fromxy(x: float, y: float) -> "Transform2d":
        return Transform2d((x, y))

    @property
    def x(self) -> float:
        return self.t[0]

    @property
    def y(self) -> float:
        return self.t[1]

    def atan2(self) -> "Rotation2d":
        return Rotation2d(atan2(self.y, self.x))

    @override
    def __str__(self) -> str:
        return f"Transform2d({self.x}m, {self.y}m)"

    @override
    def __repr__(self) -> str:
        return self.__str__()


Transform2d.ZERO = Transform2d((0, 0))
Transform2d.ONE = Transform2d((1, 1))
Transform2d.UNIT_X = Transform2d((1, 0))
Transform2d.UNIT_Y = Transform2d((0, 1))


class Rotation2d:
    ZERO: "Rotation2d"
    HALF: "Rotation2d"
    QUARTER: "Rotation2d"
    THREE_QUARTER: "Rotation2d"

    def __init__(self, theta: float) -> None:
        self.theta = theta
        self.normalize()

    def normalize(self):
        """Normalize self to be between 0 and 2pi"""
        old = self.theta
        self.theta = ((old % tau) + tau) % tau

    @staticmethod
    def from_degrees(deg: float) -> "Rotation2d":
        return Rotation2d(radians(deg))

    @property
    def degrees(self) -> float:
        return degrees(self.theta)

    @property
    def radians(self) -> float:
        return self.theta

    def sin(self) -> float:
        return sin(self.theta)

    def cos(self) -> float:
        return cos(self.theta)

    def __add__(self, other: "Rotation2d") -> "Rotation2d":
        return Rotation2d(self.theta + other.theta)

    def __neg__(self) -> "Rotation2d":
        return Rotation2d(-self.theta)

    def __sub__(self, other: "Rotation2d") -> "Rotation2d":
        return self + -other

    def __mul__(self, other: float) -> "Rotation2d":
        return Rotation2d(self.theta * other)

    def __truediv__(self, other: float) -> "Rotation2d":
        return self * (1 / other)

    @override
    def __str__(self) -> str:
        return f"{self.theta}rad"

    @override
    def __repr__(self) -> str:
        return self.__str__()


Rotation2d.ZERO = Rotation2d(0)
Rotation2d.QUARTER = Rotation2d(tau / 4)
Rotation2d.HALF = Rotation2d(tau / 2)
Rotation2d.THREE_QUARTER = Rotation2d.QUARTER + Rotation2d.HALF


class Pose2d:
    def __init__(self, t: Transform2d, r: Rotation2d):
        self.t = t
        self.r = r

    @staticmethod
    def from_trio(x: float, y: float, theta: float) -> "Pose2d":
        return Pose2d(Transform2d.fromxy(x, y), Rotation2d(theta))

    def __add__(self, other: "Rotation2d | Transform2d | Pose2d") -> "Pose2d":
        if isinstance(other, Transform2d):
            return self + Pose2d(other, Rotation2d.ZERO)
        elif isinstance(other, Rotation2d):
            return self + Pose2d(Transform2d.ZERO, other)
        else:
            return Pose2d(self.t + other.t, self.r + other.r)

    def __sub__(self, other: "Rotation2d | Transform2d | Pose2d") -> "Pose2d":
        if not isinstance(other, Pose2d):
            return self + -other
        else:
            return Pose2d(self.t - other.t, self.r - other.r)

    def __mul__(self, other: "float | Transform2d") -> "Pose2d":
        return (
            Pose2d(self.t * other, self.r * other)
            if isinstance(other, float)
            else Pose2d(self.t * other, self.r)
        )

    def __truediv__(self, other: "float | Transform2d") -> "Pose2d":
        return (
            Pose2d(self.t / other, self.r / other)
            if isinstance(other, float)
            else Pose2d(self.t / other, self.r)
        )

    @property
    def trio(self) -> tuple[float, float, float]:
        return self.t.x, self.t.y, self.r.radians

    @property
    def x(self) -> float:
        return self.t.x

    @property
    def y(self) -> float:
        return self.t.y

    @property
    def radians(self) -> float:
        return self.r.theta

    @property
    def theta(self) -> Rotation2d:
        return self.r

    @override
    def __str__(self) -> str:
        return f"Pose(x={self.x}m, y={self.y}m, θ={self.radians}rad)"

    @override
    def __repr__(self) -> str:
        return self.__str__()


class PIDController:
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        setpoint: float,
        tolerance: float,
        output_limits: tuple[float, float] = (-1.0, 1.0),
        is_angular: bool = False,
    ) -> None:
        def wrap_angle(err: float) -> float:
            return (err + pi) % tau - pi

        self.inner = PID(
            kp,
            ki,
            kd,
            setpoint=setpoint,
            scale="ms",
            output_limits=output_limits,
            error_map=wrap_angle if is_angular else None,
        )
        self.tolerance = tolerance
        self.error = float("inf")

    def calculate(self, measurement: float):
        self.error = self.inner.setpoint - measurement
        if self.inner.error_map is not None:
            self.error = self.inner.error_map(self.error)

        out = self.inner(measurement)
        return out if out is not None else 0.0

    def at_target(self):
        return abs(self.error) <= self.tolerance


def signum(x: float):
    return (x > 0) - (x < 0)
