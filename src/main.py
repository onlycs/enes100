import asyncio
import logging

from machine import UART, Pin

from libml import LibML

logging.basicConfig(level=logging.DEBUG)

led = Pin(2, Pin.OUT)
uart = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(1))
ml = LibML(uart, 154, "Fire Lord Ozai", 1201, 0)

log = logging.getLogger("FLO")


async def blink(led: Pin) -> None:
    while True:
        led.toggle()
        await asyncio.sleep_ms(500)


async def main():
    asyncio.create_task(blink(led))

    log.debug("FLO")
    await ml.handshake()
    await ml.print("Got a connection!!")  # todo: debug (ts does not work)

    while True:
        print(ml.pose())
        await asyncio.sleep_ms(500)


asyncio.run(main())
