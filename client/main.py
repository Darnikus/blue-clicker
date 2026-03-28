import socket
import time
import logging
from secrets import server_address, port

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
    while True:
        sock = None
        try:
            print(f"--- Attempting connection to {server_address} ---")
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(5) # Don't hang forever on connect
            sock.connect((server_address, port))
            sock.settimeout(None) # Go back to blocking mode
            logger.info("Connected to ESP32 (SPP)!")

            while True:
                # Example: Send a heartbeat or data
                message = "a"
                if sending_flag:
                    sock.send(message.encode('utf-8'))
                    # print(f"Time:{datetime.datetime.now()},  Sent: {message}")
                    logger.info(f"Sent: {message}")
                    
                    # If you don't receive data, the script won't know the 
                    # socket is dead until the next .send() call fails.
                    time.sleep(4 + random.randint(0, 200) / 1000)

        except socket.error as e:
            logger.error(f"Connection Lost: {e}")
            logger.error("Waiting 3 seconds before retrying...")
            if sock:
                sock.close()
            time.sleep(3)
        except KeyboardInterrupt:
            logger.error("\nUser stopped script.")
            if sock:
                sock.close()
            break

if __name__ == "__main__":
    t = threading.Thread(target=input_thread, daemon=True)
    t.start()

    connect_and_send()