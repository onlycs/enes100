# pyright: reportUndefinedVariable=false,reportIndexIssue=false,reportCallIssue=false
# ruff: noqa: F821

from time import ticks_diff, ticks_ms

import rp2
from machine import Pin

_COUNT = 15_000  # 30 ms timeout


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _trigger_pio():
    wrap_target()

    # 10 us trigger pulse
    set(pins, 1)[9]
    set(pins, 0)

    # ~65.6 ms between measurements
    set(y, 31)

    label("outer")
    set(x, 31)

    label("inner")
    nop()[31]
    jmp(x_dec, "inner")[31]
    jmp(y_dec, "outer")

    wrap()


@rp2.asm_pio()
def _echo_pio():
    pull(block)  # Load timeout counter into OSR

    wrap_target()

    # Sync to the shared trigger: wait for its falling edge
    wait(1, pin, 0)
    wait(0, pin, 0)

    # Wait up to 30 ms for rising edge
    mov(x, osr)

    label("wait_rise")
    jmp(pin, "echo_start")
    jmp(x_dec, "wait_rise")
    jmp("timeout")

    # Count duration of HIGH pulse
    label("echo_start")
    mov(x, osr)

    label("echo_high")
    jmp(pin, "count")
    jmp("done")

    label("count")
    jmp(x_dec, "echo_high")
    # falls through to timeout when x hits 0

    # No echo / pulse too long
    label("timeout")
    mov(isr, null)
    jmp("publish")

    # Successful measurement
    label("done")
    mov(isr, x)

    label("publish")
    push(noblock)
    irq(rel(0))

    wrap()


class _Echo:
    """One sensor's echo timing, synced to the shared trigger pin."""

    def __init__(self, trig: Pin, echo: int, sm_id: int) -> None:
        self.distance_cm: float = 0.0
        self.pulse_us: int = 0
        self.updated_ms: int = ticks_ms()

        self._echo = Pin(echo, Pin.IN)
        self._sm = rp2.StateMachine(
            sm_id,
            _echo_pio,
            freq=1_000_000,
            in_base=trig,
            jmp_pin=self._echo,
        )

        self._sm.irq(self._on_measurement)
        self._sm.put(_COUNT)
        self._sm.active(1)

    def _on_measurement(self, sm: rp2.StateMachine) -> None:
        # Drain any accumulated results; keep newest
        while sm.rx_fifo():
            remaining: int = sm.get()

            self.updated_ms = ticks_ms()

            if remaining == 0:
                self.pulse_us = 0
                self.distance_cm = 0.0
            else:
                self.pulse_us = (_COUNT - remaining) * 2
                self.distance_cm = self.pulse_us / 58.0

    def deinit(self) -> None:
        self._sm.irq(handler=None)
        self._sm.active(0)


class Ultrasonics:
    """Front/left/right HC-SR04s sharing one trigger pin.

    Uses 4 consecutive state machines starting at first_sm
    (trigger, front, left, right).
    """

    def __init__(
        self,
        *,
        trig: int,
        front: int,
        left: int,
        right: int,
        first_sm: int = 0,
    ) -> None:
        self._trig = Pin(trig, Pin.OUT, value=0)
        self._trigger_sm = rp2.StateMachine(
            first_sm,
            _trigger_pio,
            freq=1_000_000,
            set_base=self._trig,
        )

        self._front = _Echo(self._trig, front, first_sm + 1)
        self._left = _Echo(self._trig, left, first_sm + 2)
        self._right = _Echo(self._trig, right, first_sm + 3)

        self._trigger_sm.active(1)

    @property
    def front_cm(self) -> float:
        return self._front.distance_cm

    @property
    def left_cm(self) -> float:
        return self._left.distance_cm

    @property
    def right_cm(self) -> float:
        return self._right.distance_cm

    @property
    def age_ms(self) -> int:
        """Age of the stalest reading."""
        now = ticks_ms()
        return max(
            ticks_diff(now, self._front.updated_ms),
            ticks_diff(now, self._left.updated_ms),
            ticks_diff(now, self._right.updated_ms),
        )

    def deinit(self) -> None:
        self._trigger_sm.active(0)
        for echo in (self._front, self._left, self._right):
            echo.deinit()

        self._trig.init(Pin.OUT, value=0)
