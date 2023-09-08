from pydantic import BaseModel, model_validator
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
    left: Decimal | None
    right: Decimal | None
    login: str

    def __str__(self):
        if self.operator == Operator.fact:
            return f'{self.left}{self.operator.value}'
        if self.operator == Operator.stop:
            return f'{self.operator.value}'
        return f'{self.left} {self.operator.value} {self.right}'


    @model_validator(mode='after')
    def validate_operators(self):
        if self.operator != Operator.stop and self.left is None:
            raise ValueError('Left operand is required')
        if self.operator != Operator.fact and self.right is None:
            raise ValueError('Right operand is required')
        if self.operator == Operator.div and self.right == 0:
            raise ValueError('Division by zero')
        if self.operator == Operator.fact and self.left <= 0:
            raise ValueError('Factorial of negative number')
        if self.operator == Operator.fact and self.left > 10:
            raise ValueError('Factorial of number more than 10')
        return self
