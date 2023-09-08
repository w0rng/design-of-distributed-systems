import asyncio
import logging


logging.basicConfig(format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stop_event = asyncio.Event()


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    logger.info("Connection from %s", addr)

    data = await reader.read(100)
    message = data.decode()

    logger.debug("Received %s from %s", message, addr)
    if message == 'stop':
        logger.info("Get signal to stop server")
        stop_event.set()
        writer.close()
        await writer.wait_closed()

    logger.debug("Send: %s", message)
    writer.write(data)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(
        handler, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    logger.info('Serving on %s', addr)

    async with server:
        await server.start_serving()
        await stop_event.wait()
        logger.info("Server is stopping")


asyncio.run(main())
