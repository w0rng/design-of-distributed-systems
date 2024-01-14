import asyncio
import signal
from json import loads
from time import time

from loguru import logger

from brodcast.listen import receive_broadcast
from brodcast.send import send_broadcast
from clients_manger import ClientManager

candidate = asyncio.Queue(maxsize=10)
is_stop = asyncio.Event()
client_manager = ClientManager()

GET_DB_MESSAGE = b"get db\n"


async def client_listener():
    recive = asyncio.create_task(receive_broadcast(is_stop, candidate))
    brodcast = asyncio.create_task(send_broadcast())

    while not is_stop.is_set():
        if candidate.empty():
            await asyncio.sleep(1)
            continue
        client = candidate.get_nowait()
        await client_manager.add(client["name"], client['ip'])
        logger.info(f"add new client into db: {client['name']}")
        await asyncio.sleep(0.1)

    brodcast.cancel()
    recive.cancel()


async def client_updater():
    logger.info("start client updater")
    while not is_stop.is_set():
        for client in await client_manager.clients():

            if not client.active and time() - client.time < 60:
                continue

            try:
                reader, writer = await asyncio.open_connection(client.ip, 8888)
                writer.write(GET_DB_MESSAGE)
                await writer.drain()
            except:
                logger.info(f"{client} inactive")
                await client_manager.update(client.name, {"active": False, "time": time()})
                continue

            raw_db = loads(await reader.readuntil())
            logger.info(f"get database from {client}")
            await client_manager.merge(raw_db)

        await asyncio.sleep(10)


def stop(*args, **kwargs):
    is_stop.set()


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    logger.info(f"Connection from {addr}")

    data = await reader.readuntil()
    if data == GET_DB_MESSAGE:
        logger.info(f"{addr[0]} receive clients")
        raw_clients = ((await client_manager.dumps()) + "\n")
        logger.info(raw_clients)
        writer.write(raw_clients.encode('utf-8'))
        await writer.drain()


async def main():
    listener = asyncio.create_task(client_listener())
    updater = asyncio.create_task(client_updater())

    server = await asyncio.start_server(handler, "0.0.0.0", 8888)
    addr = server.sockets[0].getsockname()
    logger.info(f"Serving on {addr}")

    await server.start_serving()

    await is_stop.wait()
    listener.cancel()
    updater.cancel()
    server.close()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    asyncio.run(main())
