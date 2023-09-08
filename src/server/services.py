from pydantic import ValidationError

from schemas import Message, Operator
from exceptions import InvalidAuth, InvalidMessage, Stop
from math import factorial


def process_message(raw_message: str):
    try:
        message = Message.parse_raw(raw_message)
    except ValidationError as e:
        print(e)
        raise InvalidMessage()

    if not auth(message):
        raise InvalidAuth()

    return process_math(message)


def auth(message: Message):
    if message.login in list(map(str, range(0, 300))):
        return True
    return False


def process_math(message: Message):
    operator = {
        Operator.add.value: lambda x, y: x + y,
        Operator.sub.value: lambda x, y: x - y,
        Operator.mul.value: lambda x, y: x * y,
        Operator.div.value: lambda x, y: x / y,
        Operator.fact.value: lambda x, y: factorial(int(x)),
        Operator.stop.value: lambda x, y: exec("raise Stop()"),
    }[message.operator]

    return operator(message.left, message.right)
