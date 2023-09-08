import asyncio

from schemas import Message, Operator
from exceptions import InvalidAuth, Stop  # noqa
from math import factorial
import logging

logging.basicConfig(format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def process_message(raw_message: str):
    message = Message.model_validate_json(raw_message)
    logger.debug("Process %s", message)

    if not await auth(message):
        logger.info("Invalid auth")
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
    await asyncio.sleep(1)

    return operator(message.left, message.right)
