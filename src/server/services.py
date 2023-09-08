from schemas import Message, Operator
from exceptions import InvalidAuth, Stop  # noqa
from math import factorial
import asyncio


async def process_message(raw_message: str):
    message = Message.parse_raw(raw_message)

    if not await auth(message):
        raise InvalidAuth()

    return await process_math(message)


async def auth(message: Message):
    if message.login in list(map(str, range(0, 300))):
        return True
    return False


async def process_math(message: Message):
    operator = {
        Operator.add.value: lambda x, y: x + y,
        Operator.sub.value: lambda x, y: x - y,
        Operator.mul.value: lambda x, y: x * y,
        Operator.div.value: lambda x, y: x / y,
        Operator.fact.value: lambda x, y: factorial(int(x)),
        Operator.stop.value: lambda x, y: exec("raise Stop()"),
    }[message.operator]
    # await asyncio.sleep(5)

    return operator(message.left, message.right)
