"""Validation, password hashes and local/absolute time rules for Stage 1."""

import hashlib
import hmac
import math
import re
import secrets
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from json_values import clone, equal as json_equal
import legacy_model

UTC = timezone.utc
DAYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
LOCAL_PATTERN = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}'


class APIError(Exception):
    def __init__(self, status=422, code='validation_failed', message='Invalid request'):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def require(condition, status=422, code='validation_failed', message='Invalid request'):
    if not condition:
        raise APIError(status, code, message)


def obj(value):
    require(isinstance(value, dict), 400, 'malformed_request', 'Expected a JSON object')
    return value


def field(body, name, kind=str):
    require(name in body, message=f'Missing {name}')
    value = body[name]
    require(isinstance(value, kind), 400, 'malformed_request', f'Invalid type for {name}')
    return value


def identifier(value):
    require(isinstance(value, str), 400, 'malformed_request')
    require(1 <= len(value) <= 64)
    return value


def integer(value, minimum=1, ordinary_field=False):
    # JSON numbers may be written 4 or 4.0, but true is never an integer.
    if ordinary_field:
        require(type(value) in (int, float), 400, 'malformed_request')
    require(type(value) in (int, float) and (not isinstance(value, float) or math.isfinite(value))
            and value == int(value) and value >= minimum)
    return int(value)


def email(value):
    require(re.fullmatch(r'[^\s@]+@[^\s@]+', value) is not None)
    return value


def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return 'scrypt$16384$8$1$' + salt.hex() + '$' + digest.hex()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(
        r'scrypt\$16384\$8\$1\$[0-9a-f]{32}\$[0-9a-f]{128}', value) is not None


def password_matches(password, encoded):
    _, _, _, _, salt, digest = encoded.split('$')
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(actual.hex(), digest)


def local_datetime(value):
    require(isinstance(value, str), 400, 'malformed_request')
    require(re.fullmatch(LOCAL_PATTERN, value, flags=re.ASCII) is not None)
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M')
    except ValueError:
        raise APIError() from None


def local_date(value):
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value, flags=re.ASCII) is not None)
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise APIError() from None


def instant(value):
    require(isinstance(value, str))
    try:
        result = datetime.fromisoformat(value)
        require(result.tzinfo is not None)
        return result.astimezone(UTC)
    except (ValueError, OverflowError):
        raise APIError() from None


def resolve(naive, zone):
    # fold=0 chooses the first occurrence; UTC round-trip detects spring gaps.
    aware = naive.replace(tzinfo=zone, fold=0)
    try:
        require(aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == naive,
                422, 'invalid_local_time')
    except (ValueError, OverflowError):
        raise APIError() from None
    return aware


def clock_minutes(value):
    require(isinstance(value, str), 400, 'malformed_request')
    require(re.fullmatch(r'([01][0-9]|2[0-3]):[0-5][0-9]', value) is not None)
    hour, minute = map(int, value.split(':'))
    return hour * 60 + minute


def restaurants_from_fixture(items):
    require(isinstance(items, list), 400, 'malformed_request')
    restaurants, ids = [], set()
    for item in items:
        obj(item)
        rid = identifier(field(item, 'id'))
        require(rid not in ids)
        ids.add(rid)
        zone = field(item, 'timezone')
        try:
            ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError):
            raise APIError(message='Invalid timezone') from None
        r = {key: field(item, key) for key in ('id', 'name', 'timezone')}
        for key in ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes'):
            require(key in item)
            r[key] = integer(item[key], 0 if key == 'cancellation_cutoff_minutes' else 1, ordinary_field=True)
        r['opening_hours'] = []
        for hours in field(item, 'opening_hours', list):
            obj(hours)
            day = field(hours, 'weekday')
            require(day in DAYS)
            start, end = field(hours, 'opens'), field(hours, 'closes')
            require(clock_minutes(start) < clock_minutes(end))
            r['opening_hours'].append({'weekday': day, 'opens': start, 'closes': end})
        r['tables'] = []
        table_ids = set()
        for table in field(item, 'tables', list):
            obj(table)
            tid = identifier(field(table, 'id'))
            require(tid not in table_ids)
            table_ids.add(tid)
            require('capacity' in table)
            r['tables'].append({'id': tid, 'label': field(table, 'label'),
                                'capacity': integer(table['capacity'], ordinary_field=True)})
        if 'combinable' in item:
            r['combinable'], pairs = [], set()
            for pair in field(item, 'combinable', list):
                require(isinstance(pair, list), 400, 'malformed_request')
                require(len(pair) == 2)
                members = [identifier(tid) for tid in pair]
                require(len(set(members)) == 2 and all(tid in table_ids for tid in members))
                require(frozenset(members) not in pairs)
                pairs.add(frozenset(members))
                r['combinable'].append(members)
        restaurants.append(r)
    return restaurants


def restaurant(state, rid):
    identifier(rid)
    for item in state['restaurants']:
        if item['id'] == rid:
            return item
    raise APIError(404, 'not_found')


def selected_tables(record):
    return record['table_ids'] if 'table_ids' in record else [record['table_id']]


def selection(r, body):
    require(not ('table_id' in body and 'table_ids' in body))
    if 'table_id' in body:
        ids = [identifier(field(body, 'table_id'))]
    else:
        ids = [identifier(tid) for tid in field(body, 'table_ids', list)]
        require(ids and len(set(ids)) == len(ids))
    require(len(ids) <= 2, 422, 'combination_not_allowed')
    require(all(any(t['id'] == tid for t in r['tables']) for tid in ids), 404, 'not_found')
    if len(ids) == 2:
        pair = next((p for p in r.get('combinable', []) if set(p) == set(ids)), None)
        require(pair is not None, 422, 'combination_not_allowed')
        ids = list(pair)
    return ids


def selection_fields(ids):
    return {'table_ids': list(ids), **({'table_id': ids[0]} if len(ids) == 1 else {})}


def booking_fields(state, body):
    rid = identifier(field(body, 'restaurant_id'))
    require('party_size' in body)
    party = integer(body['party_size'])
    wall = local_datetime(field(body, 'starts_at_local'))
    r = restaurant(state, rid)
    ids = selection(r, body)
    capacity = sum(t['capacity'] for t in r['tables'] if t['id'] in ids)
    require(party <= capacity, 422, 'party_exceeds_capacity')
    zone = ZoneInfo(r['timezone'])
    start = resolve(wall, zone)
    try:
        end = (start.astimezone(UTC) + timedelta(minutes=r['reservation_duration_minutes'])).astimezone(zone)
    except (OverflowError, ValueError):
        raise APIError(422, 'outside_opening_hours') from None
    minute = wall.hour * 60 + wall.minute
    periods = [h for h in r['opening_hours'] if h['weekday'] == DAYS[wall.weekday()]
               and clock_minutes(h['opens']) <= minute < clock_minutes(h['closes'])]
    require(periods, 422, 'outside_opening_hours')
    grid = [h for h in periods if (minute - clock_minutes(h['opens'])) % r['slot_minutes'] == 0]
    require(grid, 422, 'not_on_slot_grid')
    fits = False
    for h in grid:
        close = datetime.combine(wall.date(), datetime.strptime(h['closes'], '%H:%M').time()).replace(tzinfo=zone, fold=0)
        if end.astimezone(UTC) <= close.astimezone(UTC):
            fits = True
    require(fits, 422, 'outside_opening_hours')
    return {'restaurant_id': rid, **selection_fields(ids), 'party_size': party,
            'starts_at_local': body['starts_at_local'], 'starts_at': start.isoformat(), 'ends_at': end.isoformat()}


def overlap(a, b):
    return (a['status'] == b['status'] == 'confirmed'
            and a['restaurant_id'] == b['restaurant_id']
            and bool(set(selected_tables(a)) & set(selected_tables(b)))
            and instant(a['starts_at']) < instant(b['ends_at'])
            and instant(b['starts_at']) < instant(a['ends_at']))


def public(reservation):
    return {k: clone(v) for k, v in reservation.items() if k != 'user_id'}


def check_cutoff(state, reservation):
    r = restaurant(state, reservation['restaurant_id'])
    # Compare elapsed minutes to avoid overflowing when given a very large cutoff.
    remaining = (instant(reservation['starts_at']) - datetime.now(UTC)).total_seconds() / 60
    require(remaining > r['cancellation_cutoff_minutes'], 409, 'cutoff_passed')


def empty_state():
    return {'schema_stage': 2, 'users': [], 'sessions': {}, 'restaurants': [], 'reservations': [], 'receipts': []}


def fixture_state(body):
    state = empty_state()
    for user in field(body, 'users', list):
        obj(user)
        uid = identifier(field(user, 'id'))
        address = email(field(user, 'email'))
        require(not any(u['id'] == uid or u['email'] == address for u in state['users']))
        state['users'].append({'id': uid, 'email': address, 'display_name': field(user, 'display_name'),
                               'password_hash': password_hash(field(user, 'password'))})
    state['restaurants'] = restaurants_from_fixture(field(body, 'restaurants', list))
    for seed in field(body, 'reservations', list):
        obj(seed)
        uid = identifier(field(seed, 'user_id'))
        require(any(u['id'] == uid for u in state['users']))
        record = booking_fields(state, seed)
        status = field(seed, 'status') if 'status' in seed else 'confirmed'
        require(status in ('confirmed', 'cancelled'))
        record.update(reservation_id=identifier(field(seed, 'id')), reference=field(seed, 'reference'),
                      user_id=uid, status=status, created_at=datetime.now(UTC).isoformat())
        require(re.fullmatch(r'[A-Z0-9]{6,12}', record['reference']) is not None)
        require(not any(r['reservation_id'] == record['reservation_id'] or r['reference'] == record['reference']
                        or overlap(r, record) for r in state['reservations']))
        state['reservations'].append(record)
    return state


def imported_state(envelope):
    """Validate detached data completely before the engine swaps its state pointer."""
    try:
        if isinstance(envelope.get('state'), dict) and 'schema_stage' not in envelope['state']:
            state = legacy_model.imported_state(envelope)
            state['schema_stage'] = 2
            for record in state['reservations']:
                record['table_ids'] = [record['table_id']]
            return state
        require(envelope['track'] == 'tablekeeper' and type(envelope['format_version']) is int
                and envelope['format_version'] == 1)
        state = clone(envelope['state'])
        require(isinstance(state, dict) and set(state) == set(empty_state()))
        require(type(state['schema_stage']) is int and state['schema_stage'] == 2)
        for key in ('users', 'restaurants', 'reservations', 'receipts'):
            require(isinstance(state[key], list))
        require(isinstance(state['sessions'], dict))
        require(json_equal(restaurants_from_fixture(state['restaurants']), state['restaurants']))
        users, emails = set(), set()
        for user in state['users']:
            require(set(user) == {'id', 'email', 'display_name', 'password_hash'})
            uid = identifier(user['id'])
            require(isinstance(user['email'], str) and isinstance(user['display_name'], str))
            email(user['email'])
            require(uid not in users and user['email'] not in emails and valid_hash(user['password_hash']))
            users.add(uid)
            emails.add(user['email'])
        for token, uid in state['sessions'].items():
            require(isinstance(token, str) and re.fullmatch(r'[A-Za-z0-9_-]{43}', token) is not None)
            require(isinstance(uid, str) and uid in users)

        def validate_reservation(record, with_owner):
            keys = {'reservation_id', 'reference', 'restaurant_id', 'party_size', 'status',
                    'starts_at_local', 'starts_at', 'ends_at', 'created_at'}
            legacy = not with_owner and 'table_ids' not in record
            if not legacy:
                keys.add('table_ids')
                require(isinstance(record['table_ids'], list) and record['table_ids'])
            if legacy or len(record['table_ids']) == 1:
                keys.add('table_id')
            if with_owner:
                keys.add('user_id')
                require(record['user_id'] in users)
            require(set(record) == keys)
            identifier(record['reservation_id'])
            require(re.fullmatch(r'[A-Z0-9]{6,12}', record['reference']) is not None)
            require(record['status'] in ('confirmed', 'cancelled'))
            request = {k: record[k] for k in ('restaurant_id', 'party_size', 'starts_at_local')}
            request['table_ids'] = selected_tables(record)
            fields = booking_fields(state, request)
            if legacy:
                fields.pop('table_ids')
            require(all(json_equal(record[k], v) for k, v in fields.items()))
            instant(record['created_at'])

        ids, refs = set(), {}
        for record in state['reservations']:
            validate_reservation(record, True)
            require(record['reservation_id'] not in ids and record['reference'] not in refs)
            ids.add(record['reservation_id'])
            refs[record['reference']] = record
        for i, record in enumerate(state['reservations']):
            require(not any(overlap(record, other) for other in state['reservations'][i + 1:]))
        scopes = set()
        for receipt in state['receipts']:
            require(set(receipt) == {'user_id', 'method', 'path', 'key', 'body', 'response'})
            require(receipt['user_id'] in users and receipt['method'] == 'POST')
            require(receipt['path'] in ('/reservations', '/reservation-moves'))
            require(isinstance(receipt['key'], str) and 1 <= len(receipt['key']) <= 255)
            require(isinstance(receipt['body'], dict) and isinstance(receipt['response'], dict))
            scope = (receipt['user_id'], receipt['method'], receipt['path'], receipt['key'])
            require(scope not in scopes)
            scopes.add(scope)
            if receipt['path'] == '/reservations':
                records = [receipt['response']]
                fields = (booking_fields if 'table_ids' in receipt['response'] else legacy_model.booking_fields)(state, receipt['body'])
                require(all(json_equal(receipt['response'].get(k), v) for k, v in fields.items()))
            else:
                require(set(receipt['response']) == {'reservations'})
                records = receipt['response']['reservations']
                moves = receipt['body'].get('moves')
                require(isinstance(moves, list) and isinstance(records, list) and 1 <= len(moves) <= 8
                        and len(moves) == len(records))
                require(len({m['reference'] for m in moves}) == len(moves))
                require(len({r['restaurant_id'] for r in records}) == 1)
                for move, record in zip(moves, records):
                    require(move['reference'] == record['reference'])
                    legacy = 'table_ids' not in record
                    for key in (('table_id',) if legacy else ()) + ('starts_at_local', 'party_size'):
                        if key in move:
                            require(json_equal(move[key], record[key]))
                    if not legacy and ('table_id' in move or 'table_ids' in move):
                        require(selection(restaurant(state, record['restaurant_id']), move) == record['table_ids'])
            for record in records:
                validate_reservation(record, False)
                current = refs[record['reference']]
                require(record['status'] == 'confirmed' and current['user_id'] == receipt['user_id'])
                for key in ('reservation_id', 'created_at', 'restaurant_id'):
                    require(record[key] == current[key])
        return state
    except (APIError, legacy_model.APIError, KeyError, TypeError, ValueError, OverflowError, AttributeError):
        raise APIError(message='Invalid state export') from None
