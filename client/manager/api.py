import asyncio

_HOST: str = "127.0.0.1"
_PORT: int = 8888


class TerminalApi:
    def __init__(self) -> None:
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, _HOST, _PORT)
        print("Server started")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                message = data.decode("utf-8").strip()

                print(message)

                writer.write(b"ACK\n")
                await writer.drain()

        except asyncio.CancelledError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()


async def main():
    a = TerminalApi()
    await a.start()

    async with a._server:
        await a._server.serve_forever()


if __name__ == "__main__":
    a = TerminalApi()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(a.stop())
