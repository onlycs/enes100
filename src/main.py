import asyncio
import logging

from machine import UART, Pin

# from flame import Flame
# from ultrasonic import HCSR04
# from motor import Motor
from libml import LibML

logging.basicConfig(level=logging.DEBUG)

uart = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(1))
ml = LibML(uart, 154, "Fire Lord Ozai", 1201, 0)

log = logging.getLogger("Mission")
# u1 = HCSR04(0, 1, sm_id=0)
# flame1 = Flame(28)


async def main():
    log.debug("FLO")
    await ml.handshake()
    await ml.print("Got a connection!!")

    while True:
        print(ml.pose())
        await asyncio.sleep_ms(500)


asyncio.run(main())
