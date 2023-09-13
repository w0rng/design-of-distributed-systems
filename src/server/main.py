import asyncio
import logging
import socket

from pydantic import ValidationError

from services import process_message
import exceptions

logging.basicConfig(format='%(asctime)s\t%(message)s')
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
        result = await process_message(message)
    except exceptions.InvalidAuth:
        await write_and_close(writer, "Invalid auth")
        return
    except exceptions.Stop:
        stop_event.set()
        logger.info("Set stop_event")
        await write_and_close(writer, "Stoping server")
        return
    except ValidationError as e:
        logger.debug("error %s", e.errors()[0]["msg"])
        await write_and_close(writer, e.errors()[0]["msg"])
        return

    logger.debug("Send: %s", result)
    await write_and_close(writer, str(result))


async def broadcast():
    interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
    all_ips = {ip[-1][0] for ip in interfaces}
    logger.info("All ips %s", all_ips)

    while not stop_event.is_set():
        for ip in all_ips:
            logger.info("Send broadcast to %s", ip)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((ip, 0))
            sock.sendto(b'i`m server', ("255.255.255.255", 5005))
            sock.close()

        await asyncio.sleep(2)

async def main():
    server = await asyncio.start_server(handler, '0.0.0.0', 8888)

    addr = server.sockets[0].getsockname()
    logger.info('Serving on %s', addr)

    async with server:
        await server.start_serving()
        asyncio.create_task(broadcast())
        await stop_event.wait()
        running_tasks = asyncio.all_tasks() - {asyncio.current_task()}
        await asyncio.gather(*running_tasks)
        logger.info("Server is stopping")


asyncio.run(main())
