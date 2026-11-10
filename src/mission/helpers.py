from typing import override

class Pose:
    KIND_FROM_ML = 0
    KIND_ROBOT_COR = 1

    def __init__(self, x: float, y: float, theta: float, kind: int = KIND_ROBOT_COR):
        self.x = x
        self.y = y
        self.theta = theta
        self.kind = kind

    def trio(self) -> tuple[float, float, float]:
        return self.x, self.y, self.theta

    def to_robot_cor(self) -> Pose:
        if self.kind == Pose.KIND_ROBOT_COR: return self
        else return Pose(self.x, self.y)

    @override
    def __str__(self) -> str:
        return f"Pose(x={self.x}m, y={self.y}m, θ={self.theta}rad, kind={'raw_ml' if self.kind == Pose.KIND_FROM_ML else 'robot'})"

    @override
    def __repr__(self) -> str:
        return self.__str__()
