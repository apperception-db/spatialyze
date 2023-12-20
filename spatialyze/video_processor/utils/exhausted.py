from typing import Generator


def exhausted(g: Generator):
    try:
        next(g)
        return False
    except StopIteration:
        return True
