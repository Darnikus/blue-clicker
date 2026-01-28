# import socket
# from secrets import *

# try:
#     # Create a Bluetooth RFCOMM socket
#     sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
#     print(f"Connecting to {server_address}...")
#     sock.connect((server_address, port))
#     print("Connected to PC1 (SPP)!")

#     while True:
#         cmd = input("Enter text to send to PC2 (or 'quit' to exit): ")
#         if cmd.lower() == 'quit':
#             break
#         # Send data (ensure no newline if your C code doesn't filter it)
#         sock.send(cmd.encode('utf-8'))

# except Exception as e:
#     print(f"Error: {e}")
# finally:
#     sock.close()



# import socket
# from pynput import keyboard
# from secrets import *

# # Bluetooth Setup
# sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
# sock.connect((server_address, port))


# for i in range(10):
#     sock.send('|'.encode('utf-8'))

# def on_press(key):
#     try:
#         # Get the character (e.g., 'w', 'a', 's', 'd')
#         char = key.char
#         sock.send(char.encode('utf-8'))
#     except AttributeError:
#         # Handle special keys like space or enter if needed
#         if key == keyboard.Key.space:
#             sock.send(' '.encode('utf-8'))

# # Start listening to your Fedora keyboard
# with keyboard.Listener(on_press=on_press) as listener:
#     print("Gaming Bridge Active. Press keys on Fedora to type on Windows...")
#     listener.join()


# import socket
# import time
# from secrets import *

# try:
#     # Create a Bluetooth RFCOMM socket
#     sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
#     print(f"Connecting to {server_address}...")
#     sock.connect((server_address, port))
#     print("Connected to PC1 (SPP)!")

#     while True:
#         # Send data (ensure no newline if your C code doesn't filter it)
#         sock.send("a".encode('utf-8'))
#         time.sleep(5)

# except Exception as e:
#     print(f"Error: {e}")
# finally:
#     sock.close()

import datetime
import socket
import time
import logging
from secrets import *

# Basic configuration: output to console, INFO level and above
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get a logger instance
logger = logging.getLogger(__name__)

def connect_and_send():
    while True:
        sock = None
        try:
            print(f"--- Attempting connection to {server_address} ---")
            sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            sock.settimeout(5) # Don't hang forever on connect
            sock.connect((server_address, port))
            sock.settimeout(None) # Go back to blocking mode
            print("Connected to ESP32 (SPP)!")

            while True:
                # Example: Send a heartbeat or data
                message = "a"
                sock.send(message.encode('utf-8'))
                # print(f"Time:{datetime.datetime.now()},  Sent: {message}")
                logger.info(f"Sent: {message}")
                
                # If you don't receive data, the script won't know the 
                # socket is dead until the next .send() call fails.
                time.sleep(5)

        except socket.error as e:
            print(f"Connection Lost: {e}")
            print("Waiting 3 seconds before retrying...")
            if sock:
                sock.close()
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nUser stopped script.")
            if sock:
                sock.close()
            break

if __name__ == "__main__":
    connect_and_send()