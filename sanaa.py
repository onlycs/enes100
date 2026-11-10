import math
import time

FRONT_SENSOR = 1
BLOCKED_DIST = 0.7  # reading below this (meters) = slot blocked
SLOT_YS = [0.5, 1.0, 1.5]  # centers of the 3 possible obstacle slots

COL1_SCAN_X = 1.0  # stop here and look at column 1 (obstacles ~x=1.4-1.6)
COL1_EXIT_X = 1.85  # point between the columns
COL2_SCAN_X = 1.85  # look at column 2 from here (obstacles ~x=2.2-2.4)
COL2_EXIT_X = 2.75  # clear of column 2

LIMBO_PREP_X = 3.2
LIMBO_PREP_Y = 1.45
LIMBO_STOP_X = 3.7

DRIVE_PWM = 160
TURN_PWM_FAST = 140
TURN_PWM_SLOW = 100

MISSION_X = 0.0
MISSION_Y = 0.0
done = False


def stop():
    tank.set_left_motor_pwm(0)
    tank.set_right_motor_pwm(0)


def wrap(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def clamp(v, lo=-255, hi=255):
    return max(lo, min(hi, v))


def face(target_theta, tol=0.05):
    """Pivot in place until facing target_theta."""
    while True:
        err = wrap(target_theta - enes100.get_theta())
        if abs(err) < tol:
            stop()
            return
        if abs(err) < 0.15:
            spd = 80
        elif abs(err) < 0.4:
            spd = TURN_PWM_SLOW
        else:
            spd = TURN_PWM_FAST
        if err > 0:
            tank.set_left_motor_pwm(-spd)
            tank.set_right_motor_pwm(spd)
        else:
            tank.set_left_motor_pwm(spd)
            tank.set_right_motor_pwm(-spd)
        time.sleep(0.02)


def go_to(tx, ty, tol=0.08):
    """Turn toward the point, then drive with heading correction."""
    while True:
        x = enes100.get_x()
        y = enes100.get_y()
        dx = tx - x
        dy = ty - y
        if math.sqrt(dx * dx + dy * dy) < tol:
            stop()
            return
        err = wrap(math.atan2(dy, dx) - enes100.get_theta())
        if abs(err) > 0.25:
            face(math.atan2(dy, dx), 0.08)
        else:
            k = 120  # steering gain
            tank.set_left_motor_pwm(clamp(DRIVE_PWM - k * err))
            tank.set_right_motor_pwm(clamp(DRIVE_PWM + k * err))
        time.sleep(0.02)


def drive_line(tx, ty, tol=0.05):
    """Face the target once, then drive a straight line holding that heading."""
    heading = math.atan2(ty - enes100.get_y(), tx - enes100.get_x())
    face(heading, 0.03)
    while True:
        dx = tx - enes100.get_x()
        dy = ty - enes100.get_y()
        reached = math.sqrt(dx * dx + dy * dy) < tol
        passed = (dx * math.cos(heading) + dy * math.sin(heading)) <= 0
        if reached or passed:
            stop()
            return
        err = wrap(heading - enes100.get_theta())
        tank.set_left_motor_pwm(clamp(DRIVE_PWM - 120 * err))
        tank.set_right_motor_pwm(clamp(DRIVE_PWM + 120 * err))
        time.sleep(0.02)


def slot_blocked():
    """Read the front sensor a few times; True if something is close ahead."""
    readings = []
    for i in range(3):
        d = tank.read_distance_sensor(FRONT_SENSOR)
        if d >= 0:
            readings.append(d)
        time.sleep(0.05)
    if len(readings) == 0:
        return False
    return min(readings) < BLOCKED_DIST


def cross_column(scan_x, exit_x):
    """Find the nearest open slot at this column and drive through it."""
    y_now = enes100.get_y()
    candidates = sorted(SLOT_YS, key=lambda s: abs(s - y_now))

    chosen = None
    for slot_y in candidates:
        go_to(scan_x, slot_y)
        face(0.0)
        time.sleep(0.1)
        if not slot_blocked():
            chosen = slot_y
            break
        enes100.print("Slot blocked at y=")
        enes100.println(slot_y)

    if chosen is None:
        chosen = 1.0  # shouldn't happen (every column has an open slot)

    enes100.print("Driving through slot y=")
    enes100.println(chosen)
    go_to(exit_x, chosen)


# MISSION SPECIFC
def setup():
    global MISSION_X, MISSION_Y
    enes100.begin("Simulator", FIRE, 3, 1116, 8, 9)
    tank.begin()
    time.sleep(0.5)

    start_x = enes100.get_x()
    start_y = enes100.get_y()

    MISSION_X = start_x
    MISSION_Y = 0.55 if start_y > 1.0 else 1.45

    enes100.print("Mission X: ")
    enes100.println(MISSION_X)
    enes100.print("Mission Y: ")
    enes100.println(MISSION_Y)


def loop():
    global done
    if done:
        stop()
        return

    # 1) Mission site
    drive_line(MISSION_X, MISSION_Y)
    enes100.println("Mission site reached. Pausing.")
    stop()
    time.sleep(2)
    # TODO: mission-specific objectives (fire sensing etc.) go here

    # 2) Obstacle column 1, then column 2
    cross_column(COL1_SCAN_X, COL1_EXIT_X)
    cross_column(COL2_SCAN_X, COL2_EXIT_X)

    # 3) Limbo
    go_to(LIMBO_PREP_X, LIMBO_PREP_Y)
    face(0.0, 0.04)
    enes100.println("Driving under limbo.")
    while enes100.get_x() < LIMBO_STOP_X:
        err = wrap(0.0 - enes100.get_theta())
        tank.set_left_motor_pwm(clamp(DRIVE_PWM - 120 * err))
        tank.set_right_motor_pwm(clamp(DRIVE_PWM + 120 * err))
        time.sleep(0.02)

    # just stop (no reverse brake pulse)
    stop()
    enes100.println("Under limbo. Stopped.")
    done = True
