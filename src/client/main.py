import asyncio
from random import choice, randint
from time import sleep
from schemas import Message, Operator


async def tcp_echo_client(message: Message):
    try:
        reader, writer = await asyncio.open_connection(
            '127.0.0.1', 8888)
    except ConnectionRefusedError:
        print("Server is not running")
        return

    print(f'Send: {message}')
    writer.write(message.json().encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()


while True:
    operator = choice(list(Operator))
    message = Message(
        operator=operator,
        left=randint(0, 10),
        right=randint(1, 10),
        login=randint(0, 350),
    )
    asyncio.run(tcp_echo_client(message))
    sleep(0.1)
