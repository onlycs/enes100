import asyncio
import logging

from machine import UART, Pin

from devices.motor import Drivetrain
from devices.servo import DS3218
from devices.ultrasonic import Ultrasonics

# from flame import Flame
# from ultrasonic import HCSR04
# from motor import Motor
from libml import LibML
from mission import StateMachine

logging.basicConfig(level=logging.DEBUG)

drive = Drivetrain(9, 8, 7, 6)
us = Ultrasonics(trig=18, left=90, right=20, front=21)
uart = UART(0, baudrate=19200, tx=Pin(16), rx=Pin(17))
ml = LibML(uart, 154, "Fire Lord Ozai", 1201, 0)
servo = DS3218(15)

machine = StateMachine(ml, [], us, drive, servo)

log = logging.getLogger("Mission")


async def main():
    await ml.handshake()
    await ml.print("Connected! Starting machine.")
    await machine.begin()


asyncio.run(main())
