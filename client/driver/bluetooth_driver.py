import asyncio
import logging
import socket
from secrets import port, server_address

logger = logging.getLogger(__name__)


class BluetoothDriver:
    def __init__(self) -> None:
        self._sock: socket.socket | None = None

        self._heartbeat_task: asyncio.Task | None = None
        self._last_activity_event: asyncio.Event = asyncio.Event()

    def disconnect(self) -> None:
        """Full disconnect used only for external shutdown."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        self._clean_socket()

        self._heartbeat_task = None

    async def send_data(self, data: str) -> bool:
        if self._sock is None:
            logger.error("There is no connection.")
            if not await self._connect():
                return False

            loop = asyncio.get_running_loop()
            if not self._heartbeat_task or self._heartbeat_task.done():
                self._heartbeat_task = loop.create_task(self._heartbeat_loop())
                logger.info("Heartbeat loop started after manual connection.")
            else:
                logger.info("Existing heartbeat loop detected and preserved.")

        # Offload the blocking socket send operation to a thread
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self._sock.sendall, data.encode("utf-8"))
            logger.info(f"Sent: {data.strip()}")
            self._last_activity_event.set()
            return True
        except Exception:
            logger.exception(f"Failed to send: {data}. Performing disconnection.")
            self._clean_socket()
            return False

    def _clean_socket(self) -> None:
        """Save socket disconnect and close."""
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

            self._sock.close()

        self._sock = None
        logger.info("Connection is closed.")

    async def _connect(self) -> bool:
        # Offload the entire blocking connection to a thread
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_connect)

    def _sync_connect(self) -> bool:
        """Internal synchronous connection method run inside the executor thread."""
        self._clean_socket()
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
            self._clean_socket()
            return False

    async def _heartbeat_loop(self) -> None:
        try:
            while True:
                if self._sock is None:
                    logger.error(
                        "Heartbeat detected dead socket. "
                        + "Attempting automatic reconnection."
                    )
                    if not await self._connect():
                        logger.error(
                            "Reconnection attempt failed. Retrying in 3 seconds..."
                        )
                        await asyncio.sleep(3)
                        continue
                    else:
                        logger.info(
                            "Automatically reconnected."
                            + " Continuing existing hearbeat loop."
                        )
                        self._last_activity_event.clear()
                        continue

                self._last_activity_event.clear()

                try:
                    # Sleeps 5 sec or wakes up instantly if event.set() is called
                    await asyncio.wait_for(
                        self._last_activity_event.wait(), timeout=5.0
                    )

                    continue  # If reached here then key was pressed
                except asyncio.TimeoutError:
                    logger.info(
                        "Connection is idle for 5 seconds. Sending heartbeat..."
                    )
                    heartbeat_msg = "\n"
                    await self.send_data(heartbeat_msg)
        except asyncio.CancelledError:
            logger.info("Heartbeat loop explicity canceled.")

    # Don't know if i need it, at least it's needed to be refactored for asyncio
    def _is_connected(self) -> bool:
        try:
            self._sock.getpeername()
            return True
        except OSError:
            logger.exception("Connection error.")
            return False
