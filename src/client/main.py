import asyncio
import socket
from random import choices, randint
from time import sleep
from schemas import Message, Operator
import logging
from socket import gaierror

logging.basicConfig(format='%(asctime)s\t%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def send_message_to(message: Message, address: str):
    try:
        reader, writer = await asyncio.open_connection(
            address, 8888)
    except ConnectionRefusedError:
        await asyncio.sleep(1)
        return
    except gaierror:
        await asyncio.sleep(1)
        return

    writer.write(message.model_dump_json().encode())
    await writer.drain()

    data = await reader.read(100)
    logger.info('%s = %s', message, data.decode())

    writer.close()
    await writer.wait_closed()


def receive_broadcast() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", 5005))
    logger.info("wait broadcast")
    _, addr = sock.recvfrom(1024)
    return addr[0]


server_address = receive_broadcast()
while True:
    operator = choices(list(Operator), weights=[100, 100, 100, 100, 100, 50])[0]
    message = Message(
        operator=operator,
        left=randint(0, 10),
        right=randint(0, 100),
        login=str(randint(0, 350)),
    )
    asyncio.run(send_message_to(message, server_address))
    sleep(0.1)
