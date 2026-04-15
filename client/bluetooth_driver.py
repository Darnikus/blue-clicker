import socket
import logging
from secrets import server_address, port
import asyncio


logger = logging.getLogger(__name__)

class BluetoothDriver:

    def __init__(self) -> None:
        self._sock: socket.socket | None = None
        self.reader = None
        self.writer = None

    async def connect(self) -> bool:
        self.disconnect()

        logger.info(f"--- Attempting connection to {server_address} ---")
        self._sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setblocking(False)

        loop = asyncio.get_running_loop()
        try:
            await asyncio.wait_for(
                loop.sock_connect(self._sock, (server_address, port)),
                timeout=10.0
            ) 
            
            self.reader, self.writer = await asyncio.open_connection(sock=self._sock)
            logger.info("Connected to ESP32 (SPP)!")
            return True
        except Exception:
            logger.exception('Failed to connect.')
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Save socket disconnect and close"""
        if self.writer:
            self.writer.close()
        
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            
            self._sock.close()
            self._sock = None
            self.reader = None
            self.writer = None
            logger.info('Connection is closed.')

    
    async def send_data(self, data: str) -> bool:
        if not self.writer or self.writer.is_closing():
            logger.error("There is not connection.")
            if not await self.connect():
                return False
        try:
            self.writer.write(data.encode('utf-8'))
            await self.writer.drain()
            logger.info(f"Sent: {data}")
            return True
        except Exception:
            logger.exception(f'Failed to send: {data}. Performing disconnection.')
            self.disconnect()
            return False

    # Don't know if i need it, at least it's needed to be refactored for asyncio
    def _is_connected(self) -> bool:
        try:
            self._sock.getpeername()
            return True
        except socket.error:
            logger.exception('Connection error.')
            return False