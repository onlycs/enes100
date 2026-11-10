# pyright: reportUndefinedVariable=false,reportIndexIssue=false,reportCallIssue=false
# ruff: noqa: F821

from time import ticks_diff, ticks_ms

import rp2
from machine import Pin

# 1 MHz PIO clock; 2 cycles per echo-count iteration
_COUNT = 15_000  # 30 ms timeout


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def _hcsr04_pio():
    pull(block)  # Load timeout counter into OSR

    wrap_target()

    # 10 us trigger pulse
    set(pins, 1)[9]
    set(pins, 0)

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
    jmp("timeout")

    # Successful measurement
    label("done")
    mov(isr, x)
    push(noblock)
    irq(rel(0))
    jmp("cooldown")

    # No echo / pulse too long
    label("timeout")
    mov(isr, null)
    push(noblock)
    irq(rel(0))

    # ~65.6 ms between measurements
    label("cooldown")
    set(y, 31)

    label("outer")
    set(x, 31)

    label("inner")
    nop()[31]
    jmp(x_dec, "inner")[31]
    jmp(y_dec, "outer")

    wrap()


class HCSR04:
    def __init__(self, trig: int, echo: int, sm_id: int = 0):
        self._distance_cm: float = 0
        self._pulse_us: int = 0
        self._updated_ms: int = 0

        self._trig = Pin(trig, Pin.OUT, value=0)
        self._echo = Pin(echo, Pin.IN)

        self._sm = rp2.StateMachine(
            sm_id,
            _hcsr04_pio,
            freq=1_000_000,
            set_base=self._trig,
            in_base=self._echo,
            jmp_pin=self._echo,
        )

        self._sm.irq(self._on_measurement)
        self._sm.put(_COUNT)
        self._sm.active(1)

    def _on_measurement(self, sm: rp2.StateMachine):
        # Drain any accumulated results; keep newest
        while sm.rx_fifo():
            remaining = sm.get()

            self._updated_ms = ticks_ms()

            if remaining == 0:
                self._pulse_us = 0
                self._distance_cm = 0
            else:
                self._pulse_us = (_COUNT - remaining) * 2
                self._distance_cm = self._pulse_us / 58.0

    @property
    def distance_cm(self):
        return self._distance_cm

    @property
    def pulse_us(self):
        return self._pulse_us

    @property
    def age_ms(self):
        return ticks_diff(ticks_ms(), self._updated_ms)

    def deinit(self):
        self._sm.irq(handler=None)
        self._sm.active(0)
        self._trig.value(0)
