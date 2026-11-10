# ruff: noqa: UP035

import asyncio
from asyncio import Task
from math import cos, degrees, radians, sin, tau
from typing import Any, Coroutine, override  # pyright: ignore[reportDeprecated]

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
    def theta(self) -> float:
        return self.r.theta

    @override
    def __str__(self) -> str:
        return f"Pose(x={self.x}m, y={self.y}m, θ={self.theta}rad)"

    @override
    def __repr__(self) -> str:
        return self.__str__()


class AsyncStack:
    def __init__(self) -> None:
        self.futures: list[Task] = []

    def append(self, *other: Coroutine[Any, Any, Any]):
        self.futures.extend(asyncio.create_task(o) for o in other)

    async def join(self):
        await asyncio.gather(*self.futures)
