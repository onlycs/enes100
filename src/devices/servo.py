from machine import PWM, Pin


class DS3218:
    def __init__(
        self,
        pin: int,
        freq: int = 50,
        min_us: int = 500,
        max_us: int = 2500,
        max_angle: float = 180.0,
    ) -> None:
        self._pwm: PWM = PWM(Pin(pin))
        self._pwm.freq(freq)
        self.min_us: int = min_us
        self.max_us: int = max_us
        self.max_angle: float = max_angle

    def write_us(self, us: int) -> None:
        us = max(self.min_us, min(self.max_us, us))
        self._pwm.duty_ns(us * 1000)

    def write_angle(self, deg: float) -> None:
        deg = max(0.0, min(self.max_angle, deg))
        us = self.min_us + (self.max_us - self.min_us) * deg / self.max_angle
        self.write_us(int(us))

    def center(self) -> None:
        self.write_us(1500)

    def release(self) -> None:
        self._pwm.duty_ns(0)

    def deinit(self) -> None:
        self._pwm.deinit()
