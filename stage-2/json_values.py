"""JSON trees without Python call-stack limits on copy, equality or encoding.

The standard decoder handles ordinary requests. A stack-based container decoder
handles deeper documents; scalar syntax is still checked by the standard library.
"""

import json
import math
import re


def clone(value):
    root = [None]
    pending = [(root, 0, value)]
    while pending:
        parent, key, current = pending.pop()
        if isinstance(current, dict):
            result = {}
            parent[key] = result
            pending.extend((result, k, v) for k, v in reversed(list(current.items())))
        elif isinstance(current, list):
            result = [None] * len(current)
            parent[key] = result
            pending.extend((result, i, v) for i, v in enumerate(current))
        else:
            parent[key] = current
    return root[0]


def equal(left, right):
    pending = [(left, right)]
    while pending:
        a, b = pending.pop()
        if type(a) in (int, float) and type(b) in (int, float):
            if a != b:
                return False
        elif type(a) is not type(b):
            return False
        elif isinstance(a, dict):
            if a.keys() != b.keys():
                return False
            pending.extend((a[k], b[k]) for k in a)
        elif isinstance(a, list):
            if len(a) != len(b):
                return False
            pending.extend(zip(a, b))
        elif a != b:
            return False
    return True


def dumps(value):
    pieces, pending = [], [('value', value)]
    while pending:
        kind, current = pending.pop()
        if kind == 'text':
            pieces.append(current)
        elif isinstance(current, (dict, list)):
            is_object = isinstance(current, dict)
            pieces.append('{' if is_object else '[')
            pending.append(('text', '}' if is_object else ']'))
            entries = list(current.items()) if is_object else list(enumerate(current))
            for i in range(len(entries) - 1, -1, -1):
                key, child = entries[i]
                pending.append(('value', child))
                if is_object:
                    if not isinstance(key, str):
                        raise ValueError('JSON object keys must be strings')
                    pending.append(('text', json.dumps(key, ensure_ascii=True) + ':'))
                if i:
                    pending.append(('text', ','))
        else:
            pieces.append(json.dumps(current, ensure_ascii=True, allow_nan=False, separators=(',', ':')))
    return ''.join(pieces)


def _invalid_constant(_value):
    raise ValueError('Non-finite JSON number')


def _finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Non-finite JSON number')
    return result


def loads(raw):
    text = raw.decode('utf-8-sig') if isinstance(raw, bytes) else raw
    decoder = json.JSONDecoder(parse_constant=_invalid_constant, parse_float=_finite_float)
    try:
        return decoder.decode(text)
    except RecursionError:
        return _decode_containers(text, decoder)


def _decode_containers(text, decoder):
    whitespace = re.compile(r'[ \t\r\n]*')
    root, pos = [None], 0
    tasks = [('value', root, 0)]
    while tasks:
        kind, target, key = tasks.pop()
        pos = whitespace.match(text, pos).end()
        char = text[pos:pos + 1]
        if kind == 'value':
            if char in ('[', '{'):
                value = [] if char == '[' else {}
                target[key] = value
                pos += 1
                tasks.append(('array' if char == '[' else 'object', value, True))
            else:
                target[key], pos = decoder.raw_decode(text, pos)
        elif kind in ('array', 'object'):
            closing = ']' if kind == 'array' else '}'
            if key and char == closing:
                pos += 1
                continue
            if kind == 'array':
                index = len(target)
                target.append(None)
            else:
                if char != '"':
                    raise ValueError('Expected object key')
                index, pos = decoder.raw_decode(text, pos)
                pos = whitespace.match(text, pos).end()
                if text[pos:pos + 1] != ':':
                    raise ValueError('Expected colon')
                pos += 1
            tasks.append((kind + '_after', target, None))
            tasks.append(('value', target, index))
        else:
            container = kind.removesuffix('_after')
            closing = ']' if container == 'array' else '}'
            if char == closing:
                pos += 1
            elif char == ',':
                pos += 1
                tasks.append((container, target, False))
            else:
                raise ValueError('Expected comma or closing delimiter')
    if whitespace.match(text, pos).end() != len(text):
        raise ValueError('Extra JSON data')
    return root[0]
