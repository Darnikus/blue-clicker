import time
import logging
from bluetooth_driver import BluetoothDriver

import asyncio
import random


sending_flag: bool = False

# Basic configuration: output to console, INFO level and above
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)

async def input_thread():
    global sending_flag
    loop = asyncio.get_running_loop()

    while True:
        cmd = await loop.run_in_executor(None, lambda: input("Type '-' to pause, '+' to resume: \n").strip().lower())
        
        if cmd == '-':
            sending_flag = False
            print("--- SENDING PAUSED ---")
        elif cmd == '+':
            sending_flag = True
            print("--- SENDING RESUMED ---")


async def connect_and_send(sock: BluetoothDriver) -> None:
    last_heartbeat = time.time()
    while True:
        try:
            message = "a"
            if sending_flag:
                if not await sock.send_data(message):
                    logger.error("Could not send data. Waiting for next cycle...")
                    await asyncio.sleep(3)
                    continue
                
                # If you don't receive data, the script won't know the 
                # socket is dead until the next .send() call fails.
                await asyncio.sleep(4 + random.randint(0, 200) / 1000)
            
            elif time.time() - last_heartbeat > 5:
                await sock.send_data('\n')
                last_heartbeat = time.time()

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            logger.error("\nUser stopped script.")
            sock.disconnect()
            break

async def main():
    sock: BluetoothDriver = BluetoothDriver()

    if not await sock.connect():
        logger.exception("Initial connection failed. Driver will try to reconnect later.")

    try:
        await asyncio.gather(
            input_thread(),
            connect_and_send(sock)
        )
    except asyncio.CancelledError:
        pass
    finally:
        sock.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        pass