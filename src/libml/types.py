class Pose:
    def __init__(self, x: float, y: float, theta: float):
        self.x = x
        self.y = y
        self.theta = theta

    def trio(self) -> tuple[float, float, float]:
        return self.x, self.y, self.theta
