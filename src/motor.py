from machine import PWM, Pin


class Motor:
    def __init__(self, pin_a: int, pin_b: int, freq: int = 20_000) -> None:
        self.a = PWM(Pin(pin_a))
        self.b = PWM(Pin(pin_b))
        self.a.freq(freq)
        self.b.freq(freq)
        self.brake()

    def set(self, speed: float):
        """Sets the motors to a speed. `speed` should be between -1.0 and 1.0, inclusive."""

        if abs(speed) > 1:
            self.set(min(max(speed, 1.0), -1.0))
            return

        duty = int(abs(speed) * (2**16 - 1))
        if speed < 0:
            self.a.duty_u16(duty)
            self.b.duty_u16(0)
        else:
            self.a.duty_u16(0)
            self.b.duty_u16(duty)

    def brake(self):
        """Sets the speed to zero"""
        self.set(0)


class Drivetrain:
    def __init__(
        self, m1a: int, m1b: int, m2a: int, m2b: int, freq: int = 20_000
    ) -> None:
        self.m1 = Motor(m1a, m1b, freq)
        self.m2 = Motor(m2a, m2b, freq)

    def set(self, m1: float, m2: float):
        """Sets the motors to a speed. Each parameter should be in between -1.0 and 1.0, inclusive."""

        self.m1.set(m1)
        self.m2.set(m2)
