import asyncio
import socket

from loguru import logger


async def send_broadcast():
    interfaces = socket.getaddrinfo(
        host=socket.gethostname(), port=None, family=socket.AF_INET
    )
    all_ips = {ip[-1][0] for ip in interfaces}
    logger.info(f"All ips {all_ips}")

    loop = asyncio.get_event_loop()

    for ip in all_ips:
        broadcast_ip = ".".join(ip.split('.')[:-1]) + ".255"
        logger.info(f"Send broadcast to {broadcast_ip}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((ip, 0))
        await loop.sock_sendto(sock, socket.gethostname().encode("utf-8"), (broadcast_ip, 5005))
        sock.close()
