import asyncio
import logging
from services import process_message
import exceptions

logging.basicConfig(format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

stop_event = asyncio.Event()


async def write_and_close(writer: asyncio.StreamWriter, message: str):
    writer.write(message.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    logger.info("Connection from %s", addr)
    if stop_event.is_set():
        await write_and_close(writer, "Server is stopping")
        return

    data = await reader.read(100)
    message = data.decode()

    logger.debug("Received %s from %s", message, addr)
    try:
        result = process_message(message)
    except exceptions.InvalidAuth:
        await write_and_close(writer, "Invalid auth")
        return
    except exceptions.InvalidMessage:
        await write_and_close(writer, "Invalid message")
        return
    except exceptions.Stop:
        stop_event.set()
        await write_and_close(writer, "Stoping server")
        return
    except Exception as e:
        logger.exception("Unexpected error")
        await write_and_close(writer, "Unexpected error")
        return

    logger.debug("Send: %s", result)
    await write_and_close(writer, str(result))


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
