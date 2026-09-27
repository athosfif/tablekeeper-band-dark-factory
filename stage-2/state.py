"""JSON-only state, constructed and validated before atomic replacement."""
from copy import deepcopy
import json
from datetime import datetime

from domain import available, proposal, reference, restaurant_config
from security import hash_password, valid_hash
from timekeeping import now
from validation import APIError, email, field, identifier, object_body, require, same_json

STATE_KEYS = {'users', 'restaurants', 'reservations', 'tokens', 'receipts'}
RECORD_KEYS = {'reservation_id', 'reference', 'restaurant_id', 'table_id', 'party_size',
               'status', 'starts_at_local', 'starts_at', 'ends_at', 'created_at', 'user_id'}


def empty_state():
    return {key: {} for key in STATE_KEYS}


def fixture_state(body):
    state = empty_state()
    emails = set()
    for user in field(body, 'users', list):
        object_body(user)
        uid, address = identifier(user, 'id'), email(user)
        password = field(user, 'password', str)
        require(len(password) >= 8)
        require(uid not in state['users'] and address not in emails)
        state['users'][uid] = {'id': uid, 'email': address,
                               'display_name': field(user, 'display_name', str),
                               'password_hash': hash_password(password)}
        emails.add(address)
    for entry in field(body, 'restaurants', list):
        restaurant = restaurant_config(entry)
        require(restaurant['id'] not in state['restaurants'])
        state['restaurants'][restaurant['id']] = restaurant
    ids = set()
    for body in field(body, 'reservations', list):
        object_body(body)
        candidate = proposal(state['restaurants'], body)
        uid = identifier(body, 'user_id')
        rid = identifier(body, 'id')
        ref = reference(field(body, 'reference', str))
        require(uid in state['users'] and rid not in ids and ref not in state['reservations'])
        require(available(candidate, state['reservations']), 'table_unavailable', 409)
        state['reservations'][ref] = {**candidate, 'reservation_id': rid, 'reference': ref,
                                      'user_id': uid, 'status': 'confirmed', 'created_at': now().isoformat()}
        ids.add(rid)
    return state


def validate_record(record, state, *, owner=None):
    require(type(record) is dict and set(record) == RECORD_KEYS)
    identifier(record, 'reservation_id')
    reference(record['reference'])
    require(record['user_id'] in state['users'])
    if owner is not None:
        require(record['user_id'] == owner)
    require(record['status'] in ('confirmed', 'cancelled'))
    expected = proposal(state['restaurants'], record)
    require(all(same_json(record[k], v) for k, v in expected.items()))
    created = datetime.fromisoformat(field(record, 'created_at', str))
    require(created.tzinfo is not None)


def imported_state(envelope):
    """An invalid snapshot never escapes into the live store, including malformed internals."""
    try:
        require(envelope.get('track') == 'tablekeeper')
        require(type(envelope.get('format_version')) is int and envelope['format_version'] == 1)
        candidate = envelope.get('state')
        require(type(candidate) is dict and set(candidate) == STATE_KEYS)
        require(all(type(v) is dict for v in candidate.values()))
        state = deepcopy(candidate)
        emails = set()
        for uid, user in state['users'].items():
            require(type(user) is dict and set(user) == {'id', 'email', 'display_name', 'password_hash'})
            require(identifier(user, 'id') == uid)
            address = email(user)
            require(address not in emails)
            emails.add(address)
            field(user, 'display_name', str)
            require(valid_hash(user['password_hash']))
        for rid, restaurant in state['restaurants'].items():
            validated = restaurant_config(restaurant)
            require(validated['id'] == rid and same_json(validated, restaurant))
        for token, uid in state['tokens'].items():
            require(type(token) is str and bool(token) and type(uid) is str and uid in state['users'])
        checked = {}
        ids = set()
        for ref, reservation in state['reservations'].items():
            validate_record(reservation, state)
            require(ref == reservation['reference'] and reservation['reservation_id'] not in ids)
            ids.add(reservation['reservation_id'])
            if reservation['status'] == 'confirmed':
                require(available(reservation, checked))
            checked[ref] = reservation
        for namespace, receipt in state['receipts'].items():
            parts = json.loads(namespace)
            require(type(parts) is list and len(parts) == 4 and all(type(p) is str for p in parts))
            uid, method, path, key = parts
            require(namespace == receipt_key(uid, path, key))
            require(uid in state['users'] and method == 'POST'
                    and path in ('/reservations', '/reservation-moves') and 1 <= len(key) <= 255)
            require(type(receipt) is dict and set(receipt) == {'body', 'response'})
            object_body(receipt['body'])
            response = receipt['response']
            if path == '/reservation-moves':
                require(type(response) is dict and set(response) == {'reservations'})
                records = field(response, 'reservations', list)
                require(1 <= len(records) <= 8)
            else:
                records = [response]
            for record in records:
                validate_record({**record, 'user_id': uid}, state, owner=uid)
                current = state['reservations'][record['reference']]
                require(current['reservation_id'] == record['reservation_id']
                        and current['created_at'] == record['created_at'] and current['user_id'] == uid)
        return state
    except (APIError, ValueError, TypeError, KeyError, OverflowError, RecursionError):
        from validation import fail
        fail('validation_failed', 422, 'Invalid portable state')


def receipt_key(uid, path, key):
    return json.dumps([uid, 'POST', path, key], ensure_ascii=True, separators=(',', ':'))
