# ruff: noqa: UP035
from typing import Callable, Generator  # pyright: ignore[reportDeprecated]

from libml.op import MissionCandles
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


def helper_require_pose(
    ins: Inputs | None = None,
) -> Generator[Outputs, Inputs, Pose2d]:
    if ins is None:
        ins = yield Outputs()

    x = 0
    while ins.pose is None:
        messages = ["Lost! Vision system cannot see us!"] if x == 0 else []
        ins = yield Outputs(messages=messages)
        x += 1
        x %= 10

    return ins.pose


def helper_wait_ms(
    millis: int, callback: Callable[[Inputs], None] = lambda ins: None
) -> Generator[Outputs, Inputs, int]:
    waited = 0
    while waited < millis:
        ins = yield Outputs()

        callback(ins)
        waited += ins.dt

    return waited


def helper_rotate_to(theta: Rotation2d) -> Generator[Outputs, Inputs, Inputs]:
    pid = PIDController(
        TURN_KP, TURN_KI, TURN_KD, theta.radians, TURN_TOLERANCE, is_angular=True
    )

    ins = yield Outputs()
    while not pid.at_target():
        pose = yield from helper_require_pose(ins)
        calc = pid.calculate(pose.radians)
        ins = yield Outputs(motors=(-calc, calc))

    return ins


def helper_translate(dist: float) -> Generator[Outputs, Inputs, Inputs]:
    pid = PIDController(DRIVE_KP, DRIVE_KI, DRIVE_KD, dist, DRIVE_TOLERANCE)

    ins = yield Outputs()
    initial = (yield from helper_require_pose(ins)).transform

    while not pid.at_target():
        current = (yield from helper_require_pose(ins)).transform
        diff = (initial - current).hypot()
        output = pid.calculate(diff)
        ins = yield Outputs(motors=(output, output))

    return ins


def helper_navigate(to: Pose2d) -> Generator[Outputs, Inputs, Inputs]:
    initial = yield from helper_require_pose()
    atan = (to.transform - initial.transform).atan2()
    yield from helper_rotate_to(atan)
    return (yield from helper_translate((initial.transform - to.transform).hypot()))


MISSION_LINE_X = 0.5
ARENA_HEIGHT = 2.0


def to_mission_site() -> Routine:
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
        calc = pid.calculate(ins.us.front_cm)
        ins = yield Outputs(motors=(-calc, -calc))

    # TODO: ML!!!!
    return perform_mission()


def perform_mission() -> Routine:
    SERVO_MILLIS = 5000

    ins = yield Outputs(servo_degrees=180)
    flames = list(ins.flames)

    def update_flames(ins: Inputs):
        for i, fl in enumerate(ins.flames):
            flames[i] = flames[i] or fl

    yield from helper_wait_ms(SERVO_MILLIS, update_flames)
    total = sum(flames)

    yield Outputs(messages=[MissionCandles(total)], servo_degrees=180)
    yield from helper_wait_ms(SERVO_MILLIS)

    yield from helper_navigate(Pose2d.from_trio(MISSION_LINE_X, ARENA_HEIGHT / 2, 0))
    yield from helper_translate(0.05)

    return navigate_rows()


def navigate_rows(row: int = 0) -> Routine:
    """Row should be [0, 1] inclusive"""

    BETWEEN_OBS = 0.5
    BETWEEN_ROWS = 0.8

    ins = yield from helper_translate(BETWEEN_ROWS)

    if ins.us.front_cm <= 10:
        # try turning upfield
        yield from helper_rotate_to(Rotation2d.QUARTER)
        ins = yield from helper_translate(BETWEEN_OBS)

        if ins.us.right_cm <= 10:
            yield from helper_rotate_to(Rotation2d.THREE_QUARTER)
            yield from helper_translate(BETWEEN_OBS * 2)

        yield from helper_rotate_to(Rotation2d.ZERO)

    if row == 1:
        return navigate_to_end()

    return navigate_rows(1)


def navigate_to_end() -> Routine:
    yield from helper_translate(0.5)
    yield from helper_navigate(Pose2d.from_trio(0.8 + 2, 3 * ARENA_HEIGHT / 4, 0))
    yield from helper_translate(1)

    return final()


def final() -> Routine:
    """Since the state machine doesn't handle stopping, we can return this in order to effectively stop the machine"""
    yield Outputs(messages=["Program completed"], motors=(0, 0))

    while True:
        yield Outputs()
