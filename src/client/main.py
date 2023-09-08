import asyncio
from random import random
from time import sleep


async def tcp_echo_client(message):
    try:
        reader, writer = await asyncio.open_connection(
            '127.0.0.1', 8888)
    except ConnectionRefusedError:
        print("Server is not running")
        return

    print(f'Send: {message!r}')
    writer.write(message.encode())
    await writer.drain()

    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')

    print('Close the connection')
    writer.close()
    await writer.wait_closed()


while True:
    message = 'Hello World!' if random() > 0.005 else 'stop'
    asyncio.run(tcp_echo_client(message))
    if message == 'stop':
        break
    sleep(0.1)