from machine import Pin


class Flame:
    def __init__(self, pin: int) -> None:
        self.pin = Pin(pin, Pin.IN)

    def read(self):
        return self.pin.value() == 0
