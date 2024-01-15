import asyncio
import socket

from loguru import logger


async def receive_broadcast(stop_event: asyncio.Event, connections: asyncio.Queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", 5005))
    sock.setblocking(False)

    loop = asyncio.get_event_loop()

    while not stop_event.is_set():
        logger.info("wait broadcast")
        data, addr = await loop.sock_recvfrom(sock, 1024)
        if data == b"metrics":
            sock.sendto(socket.gethostname().encode("utf-8"), addr)
            continue

        logger.info(f"receive broadcast from {addr[0]}")

        await connections.put({"name": data.decode('utf-8'), "ip": addr[0]})
