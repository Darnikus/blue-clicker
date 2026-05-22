import asyncio
import logging
import socket
from secrets import port, server_address

logger = logging.getLogger(__name__)


class BluetoothDriver:
    def __init__(self) -> None:
        self._sock: socket.socket | None = None

    async def _connect(self) -> bool:
        # Offload the entire blocking connection to a thread
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_connect)

    def _sync_connect(self) -> bool:
        """Internal synchronous connection method run inside the executor thread."""
        self.disconnect()
        logger.info(f"--- Attempting connection to {server_address} ---")

        try:
            self._sock = socket.socket(
                socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
            )
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(10.0)  # 10-second timeout for the connection block

            self._sock.connect((server_address, port))
            logger.info("Connected to ESP32 (SPP)!")
            return True
        except Exception:
            logger.exception("Failed to connect.")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Save socket disconnect and close"""
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            self._sock.close()

        self._sock = None
        logger.info("Connection is closed.")

    async def send_data(self, data: str) -> bool:
        if self._sock is None:
            logger.error("There is no connection.")
            if not await self._connect():
                return False

        # Offload the blocking socket send operation to a thread
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._sock.sendall, data.encode("utf-8"))
            logger.info(f"Sent: {data.strip()}")
            return True
        except Exception:
            logger.exception(f"Failed to send: {data}. Performing disconnection.")
            self.disconnect()
            return False

    # Don't know if i need it, at least it's needed to be refactored for asyncio
    def _is_connected(self) -> bool:
        try:
            self._sock.getpeername()
            return True
        except OSError:
            logger.exception("Connection error.")
            return False
