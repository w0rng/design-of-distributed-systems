import asyncio
from random import choices, randint
from time import sleep
from schemas import Message, Operator
import logging
from socket import gaierror

logging.basicConfig(format='%(asctime)s\t%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def tcp_echo_client(message: Message):
    try:
        reader, writer = await asyncio.open_connection(
            'server', 8888)
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


while True:
    operator = choices(list(Operator), weights=[100, 100, 100, 100, 100, 20])[0]
    message = Message(
        operator=operator,
        left=randint(0, 10),
        right=randint(0, 100),
        login=str(randint(0, 350)),
    )
    asyncio.run(tcp_echo_client(message))
    sleep(0.1)
