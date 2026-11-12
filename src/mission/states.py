# ruff: noqa: UP035
from typing import Generator  # pyright: ignore[reportDeprecated]

from mission.helpers import PIDController, Pose2d, Rotation2d, signum
from mission.io import Inputs, Outputs, Routine

DRIVE_KP = 0.0
DRIVE_KI = 0.0
DRIVE_KD = 0.0
DRIVE_TOLERANCE = 0.0

TURN_KP = 0.0
TURN_KI = 0.0
TURN_KD = 0.0
TURN_TOLERANCE = 0.0

US_KP = 0.0
US_KI = 0.0
US_KD = 0.0
US_TOLERANCE = 0.0


def helper_require_pose(ins: Inputs) -> Generator[Outputs, Inputs, Pose2d]:
    x = 0

    while ins.pose is None:
        messages = ["Lost! Vision system cannot see us!"] if x == 0 else []
        ins = yield Outputs(messages=messages)
        x += 1
        x %= 10

    return ins.pose


def to_mission_site() -> Routine:
    MISSION_LINE_X = 0.5
    ABS_MISSION_FACING = Rotation2d.QUARTER
    MISSION_US = 0.0

    ins = yield Outputs()
    pid = PIDController(DRIVE_KP, DRIVE_KI, DRIVE_KD, MISSION_LINE_X, DRIVE_TOLERANCE)
    initial_pose = yield from helper_require_pose(ins)

    while not pid.at_target():
        pose = yield from helper_require_pose(ins)
        calc = pid.calculate(pose.x)
        output = calc * signum(pose.theta.cos())
        ins = yield Outputs(motors=(output, output))

    ins = yield Outputs(motors=(0, 0))
    side: float = 1.0 if initial_pose.y < 1.0 else -1.0

    sp = (ABS_MISSION_FACING * side).radians
    pid = PIDController(TURN_KP, TURN_KI, TURN_KD, sp, TURN_TOLERANCE)
    while not pid.at_target():
        pose = yield from helper_require_pose(ins)
        calc = pid.calculate(pose.radians)
        ins = yield Outputs(motors=(-calc, calc))

    pid = PIDController(US_KP, US_KI, US_KD, MISSION_US, US_TOLERANCE)
    while not pid.at_target():
        calc = pid.calculate(ins.us.front)
        ins = yield Outputs(motors=(-calc, -calc))

    return final


def final() -> Routine:
    """Since the state machine doesn't handle stopping, we can return this in order to effectively stop the machine"""
    yield Outputs(messages=["Program completed"], motors=(0, 0))

    while True:
        yield Outputs()
