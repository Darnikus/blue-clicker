import socket
import logging
import time
from secrets import server_address, port


logger = logging.getLogger(__name__)

class BluetoothDriver:

    def __init__(self) -> None:
        self._sock: socket.socket | None = None

    def connect(self) -> bool:
        self.disconnect()
        time.sleep(5)

        logger.info(f"--- Attempting connection to {server_address} ---")
        try:
            self._sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(10) # Don't hang forever on connect
            self._sock.connect((server_address, port))
            self._sock.settimeout(None) # Go back to blocking mode

            logger.info("Connected to ESP32 (SPP)!")
            return True
        except socket.error:
            logger.exception('Failed to connect.')
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Save socket disconnect and close"""
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            
            self._sock.close()
            self._sock = None
            logger.info('Connection is closed.')

    
    def send_data(self, data: str) -> bool:
        if not self._sock:
            logger.error("There is not connection.")
            if not self.connect():
                return False
        try:
            self._sock.send(data.encode('utf-8'))
            logger.info(f"Sent: {data}")
            return True
        except socket.error:
            logger.exception(f'Failed to send: {data}. Performing disconnection.')
            self.disconnect()
            return False

    def _is_connected(self) -> bool:
        try:
            self._sock.getpeername()
            return True
        except socket.error:
            logger.exception('Connection error.')
            return False