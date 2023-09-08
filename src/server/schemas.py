from pydantic import BaseModel, root_validator, ValidationError
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
            return f'{self.operator}{self.left}'
        if self.operator == Operator.stop:
            return f'{self.operator}'
        return f'{self.left}{self.operator}{self.right}'

    @root_validator
    def validate_operators(cls, values):
        if values['operator'] != Operator.stop and values['left'] is None:
            raise ValueError('Left operand is required')
        if values['operator'] != Operator.fact and values['right'] is None:
            raise ValueError('Right operand is required')
        if values['operator'] == Operator.div and values['right'] == 0:
            raise ValueError('Division by zero')
        if values['operator'] == Operator.fact and values['left'] <= 0:
            raise ValueError('Factorial of negative number')
        if values['operator'] == Operator.fact and values['left'] > 10:
            raise ValueError('Factorial of number more than 10')
        return values
