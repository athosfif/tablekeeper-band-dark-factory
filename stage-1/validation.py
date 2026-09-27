"""The API's type, format and domain-error boundary."""
import math
import re


class APIError(Exception):
    def __init__(self, status, code, message=None):
        self.status = status
        self.code = code
        self.message = message or code.replace('_', ' ').capitalize()
        super().__init__(self.message)


def fail(code='validation_failed', status=422, message=None):
    raise APIError(status, code, message)


def require(condition, code='validation_failed', status=422):
    if not condition:
        fail(code, status)


def object_body(value):
    require(isinstance(value, dict), 'malformed_request', 400)
    return value


def field(body, name, kind, *, maximum=None):
    require(name in body)
    value = body[name]
    require(type(value) is kind, 'malformed_request', 400)
    if maximum is not None:
        require(len(value) <= maximum)
    return value


def identifier(body, name):
    value = field(body, name, str, maximum=64)
    require(bool(value))
    return value


def integer(body, name, minimum=1):
    value = field(body, name, int)
    require(value >= minimum)
    return value


def party(body):
    value = body.get('party_size')
    require(type(value) in (int, float) and math.isfinite(value)
            and value >= 1 and value == int(value))
    return int(value)


def email(body):
    value = field(body, 'email', str)
    require(re.fullmatch(r'[^\s@]+@[^\s@]+', value) is not None)
    return value


def same_json(left, right):
    """JSON value equality: object order immaterial, booleans are not numbers."""
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right
