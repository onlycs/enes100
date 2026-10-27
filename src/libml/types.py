class Pose:
    def __init__(self, x: float, y: float, theta: float):
        self.x = x
        self.y = y
        self.theta = theta

    def trio(self) -> tuple[float, float, float]:
        return self.x, self.y, self.theta

    def __str__(self) -> str:
        return f"Pose(x={self.x}m, y={self.y}m, θ={self.theta}rad"

    def __repr__(self) -> str:
        return self.__str__()
