from typing import Union

Number = Union[int, float]

def add(a: Number, b:Number) -> Number:
    result = a + b
    return result

def subtract(a: Number, b: Number) -> Number:
    result = a - b
    return result

def multiply(a: Number, b: Number) -> Number:
    result = a * b
    return result

def divide(a: Number, b: Number) -> Number:
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    
    result = a / b
    return result