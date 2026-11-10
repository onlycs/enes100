from flame import Flame
from libml import LibML
from mission.io import State
from mission.states import InitialState
from ultrasonic import HCSR04


class StateMachine:
    def __init__(self, ml: LibML, flames: list[Flame], ultrasonics: list[HCSR04]):
        self.state: State = InitialState.create()
