import time
import logging
from bluetooth_driver import BluetoothDriver

import asyncio
import random

from shell import SessionShell


# sending_flag: bool = False

# # Basic configuration: output to console, INFO level and above
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)

# async def input_thread() -> None:
#     global sending_flag
#     loop = asyncio.get_running_loop()

#     while True:
#         cmd = await loop.run_in_executor(None, lambda: input("Type '-' to pause, '+' to resume: \n").strip().lower())
        
#         if cmd == '-':
#             sending_flag = False
#             print("--- SENDING PAUSED ---")
#         elif cmd == '+':
#             sending_flag = True
#             print("--- SENDING RESUMED ---")


# async def connect_and_send(driver: BluetoothDriver) -> None:
#     last_heartbeat = time.time()
#     while True:
#         try:
#             message = "a"
#             if sending_flag:
#                 if not await driver.send_data(message):
#                     logger.error("Could not send data. Waiting for next cycle...")
#                     await asyncio.sleep(3)
#                     continue
                
#                 # If you don't receive data, the script won't know the 
#                 # socket is dead until the next .send() call fails.
#                 await asyncio.sleep(4 + random.randint(0, 200) / 1000)
            
#             elif time.time() - last_heartbeat > 5:
#                 await driver.send_data('\n')
#                 last_heartbeat = time.time()
#                 await asyncio.sleep(0.1)
            
#             else:
#                 await asyncio.sleep(0.01)

#         except KeyboardInterrupt:
#             logger.error("\nUser stopped script.")
#             driver.disconnect()
#             break

async def main() -> None:
    driver: BluetoothDriver = BluetoothDriver()
    shell: SessionShell = SessionShell()

    await shell.run()
    # if not await driver.connect():
    #     logger.exception("Initial connection failed. Driver will try to reconnect later.")

    # try:
    #     await asyncio.gather(
    #         input_thread(),
    #         connect_and_send(driver)
    #     )
    # except asyncio.CancelledError:
    #     pass
    # finally:
    #     driver.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        pass