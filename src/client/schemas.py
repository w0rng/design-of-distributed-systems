from pydantic import BaseModel
from decimal import Decimal
from enum import Enum


class Operator(str, Enum):
    add = '+'
    sub = '-'
    mul = '*'
    div = '/'
    fact = '!'
    stop = 'stop'


class Message(BaseModel):
    operator: Operator
    left: Decimal
    right: Decimal
    login: str

    def __str__(self):
        if self.operator == Operator.fact:
            return f'{self.left}{self.operator.value}'
        if self.operator == Operator.stop:
            return f'{self.operator.value}'
        return f'{self.left} {self.operator.value} {self.right}'
