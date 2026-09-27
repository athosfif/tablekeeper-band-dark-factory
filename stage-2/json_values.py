"""Lossless JSON numbers for complete request identity and portable receipts.

Unknown fields still belong to the idempotency body. Binary floats would merge
distinct decimal values, or overflow an otherwise valid JSON number to infinity.
"""
from decimal import Decimal
import json


def reject_constant(value):
    raise ValueError('Non-JSON number')


def loads(value):
    return json.loads(value, parse_float=Decimal, parse_constant=reject_constant)


def dumps(value):
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('Non-JSON number')
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=True) + ':' + dumps(v)
                              for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(dumps(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
