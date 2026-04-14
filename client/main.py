import time
import logging
from bluetooth_driver import BluetoothDriver

import threading
import random


sending_flag: bool = False

# Basic configuration: output to console, INFO level and above
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)

def input_thread():
    global sending_flag
    while True:
        cmd = input("Type '-' to pause, '+' to resume: \n").strip().lower()
        if cmd == '-':
            sending_flag = False
            print("--- SENDING PAUSED ---")
        elif cmd == '+':
            sending_flag = True
            print("--- SENDING RESUMED ---")


def connect_and_send():
    sock: BluetoothDriver = BluetoothDriver()

    last_heartbeat = time.time()
    while True:
        try:
            while True:
                message = "a"
                if sending_flag:
                    if not sock.send_data(message):
                        logger.error("Could not send data. Waiting for next cycle...")
                        time.sleep(3)
                        continue
                    
                    # If you don't receive data, the script won't know the 
                    # socket is dead until the next .send() call fails.
                    time.sleep(4 + random.randint(0, 200) / 1000)
                
                elif time.time() - last_heartbeat > 5:
                    sock.send_data('\n')
                    last_heartbeat = time.time()

        except KeyboardInterrupt:
            logger.error("\nUser stopped script.")
            sock.disconnect()
            break

if __name__ == "__main__":
    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    connect_and_send()