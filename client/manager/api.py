import asyncio
import json
import logging

from driver.bluetooth_driver import BluetoothDriver
from manager.protocol import InvalidActionError, ProtocolMessage

_HOST: str = "127.0.0.1"
_PORT: int = 8888
logger = logging.getLogger(__name__)


class TerminalApi:
    def __init__(self, driver: BluetoothDriver) -> None:
        self._driver: BluetoothDriver = driver
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, _HOST, _PORT)
        logger.info(f"Server is listening on {_HOST}:{_PORT}")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._driver.disconnect()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            while True:
                request = await reader.readline()
                if not request:
                    break

                try:
                    request_message = ProtocolMessage.deserialize(request)
                    logger.info(
                        f"Received: Action: {request_message.action}, "
                        + f"Payload: {request_message.payload}"
                    )

                    if not await self._driver.send_data(request_message.serialize()):
                        logger.error(
                            f"Driver failed to send key: '{request_message.payload}'."
                        )
                        status = "error"
                        message = "Failed to send key"
                    else:
                        status = "success"
                        message = "Message received successfully"

                    response = {
                        "status": status,
                        "message": message,
                        "data": request_message.payload,
                    }

                except InvalidActionError as e:
                    logger.exception(
                        f"Received request has unknown action: {e.invalid_action}."
                    )
                    response = {
                        "status": "error",
                        "message": f"Unknown action: {e.invalid_action}",
                    }
                except ValueError as e:
                    logger.exception(str(e))
                    response = {
                        "status": "error",
                        "message": "Invalid JSON format",
                    }

                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()

        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
