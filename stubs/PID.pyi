from typing import Callable, Literal

_Scale = Literal["s", "ms", "us", "ns", "cpu"]
_Limits = tuple[float | None, float | None]

class PID:
    Kp: float
    Ki: float
    Kd: float
    setpoint: float
    sample_time: float | None
    scale: _Scale
    proportional_on_measurement: bool
    error_map: Callable[[float], float] | None

    def __init__(
        self,
        Kp: float = 1.0,
        Ki: float = 0.0,
        Kd: float = 0.0,
        setpoint: float = 0,
        sample_time: float | None = None,
        scale: _Scale = "s",
        output_limits: _Limits | list[float | None] = ...,
        auto_mode: bool = True,
        proportional_on_measurement: bool = False,
        error_map: Callable[[float], float] | None = None,
    ) -> None: ...
    def __call__(self, input_: float, dt: float | None = None) -> float | None: ...
    @property
    def components(self) -> tuple[float, float, float]: ...
    @property
    def tunings(self) -> tuple[float, float, float]: ...
    @tunings.setter
    def tunings(self, tunings: tuple[float, float, float]) -> None: ...
    @property
    def auto_mode(self) -> bool: ...
    @auto_mode.setter
    def auto_mode(self, enabled: bool) -> None: ...
    def set_auto_mode(
        self, enabled: bool, last_output: float | None = None
    ) -> None: ...
    @property
    def output_limits(self) -> _Limits: ...
    @output_limits.setter
    def output_limits(self, limits: _Limits | list[float | None] | None) -> None: ...
    def reset(self) -> None: ...
