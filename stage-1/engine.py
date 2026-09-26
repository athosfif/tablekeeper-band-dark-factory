"""One lock is the transaction boundary for reads, writes, snapshots and receipts."""

import copy
import re
import secrets
import threading
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from model import (APIError, DAYS, UTC, booking_fields, check_cutoff, clock_minutes, email,
                   empty_state, field, fixture_state, identifier, imported_state, instant,
                   integer, json_equal, local_date, overlap, password_hash, password_matches,
                   public, require)


class Engine:
    def __init__(self):
        self.state = empty_state()
        self.lock = threading.RLock()

    def handle(self, method, path, query, headers, body):
        with self.lock:
            status, value = self.dispatch(method, path, query, headers, body)
            # Never expose mutable state after releasing the transaction lock.
            return status, copy.deepcopy(value)

    def authenticate(self, headers):
        auth = headers.get('Authorization', '')
        match = re.fullmatch(r'Bearer ([^\s]+)', auth, flags=re.IGNORECASE)
        uid = self.state['sessions'].get(match[1]) if match else None
        require(uid is not None, 401, 'unauthenticated')
        return uid

    def owned(self, reference, uid):
        record = next((r for r in self.state['reservations']
                       if r['reference'] == reference and r['user_id'] == uid), None)
        require(record is not None, 404, 'not_found')
        return record

    def amendment(self, record, changes):
        require(record['status'] != 'cancelled', 409, 'reservation_cancelled')
        check_cutoff(self.state, record)
        merged = {k: changes.get(k, record[k]) for k in ('table_id', 'starts_at_local', 'party_size')}
        merged['restaurant_id'] = record['restaurant_id']
        fields = booking_fields(self.state, merged)
        return {**record, **fields}

    def ensure_available(self, replacements):
        ids = {r['reservation_id'] for r in replacements}
        unlisted = [r for r in self.state['reservations'] if r['reservation_id'] not in ids]
        for i, record in enumerate(replacements):
            require(not any(overlap(record, r) for r in unlisted + replacements[i + 1:]),
                    409, 'table_unavailable')

    def replace(self, records):
        by_id = {r['reservation_id']: r for r in records}
        self.state['reservations'] = [by_id.get(r['reservation_id'], r) for r in self.state['reservations']]

    def receipt(self, uid, method, path, headers, body):
        key = headers.get('Idempotency-Key')
        require(key is not None and key != '', 400, 'missing_idempotency_key')
        require(1 <= len(key) <= 255)
        for receipt in self.state['receipts']:
            if (receipt['user_id'], receipt['method'], receipt['path'], receipt['key']) == (uid, method, path, key):
                require(json_equal(receipt['body'], body), 409, 'idempotency_key_reuse')
                return receipt['response'], key
        return None, key

    def dispatch(self, method, path, query, headers, body):
        state = self.state
        if method == 'GET' and path == '/health':
            return 200, {'status': 'ok'}
        if method == 'POST' and path == '/_test/reset':
            self.state = fixture_state(body)
            return 204, None
        if method == 'GET' and path == '/_test/export':
            return 200, {'track': 'tablekeeper', 'format_version': 1, 'state': state}
        if method == 'POST' and path == '/_test/import':
            self.state = imported_state(body)
            return 204, None
        if method == 'POST' and path in ('/auth/signup', '/auth/login'):
            address, password = field(body, 'email'), field(body, 'password')
            email(address)
            user = next((u for u in state['users'] if u['email'] == address), None)
            if path == '/auth/signup':
                name = field(body, 'display_name')
                require(len(password) >= 8)
                require(user is None, 409, 'email_taken')
                user = {'id': 'u_' + uuid.uuid4().hex, 'email': address, 'display_name': name,
                        'password_hash': password_hash(password)}
                state['users'].append(user)
            else:
                require(user is not None and password_matches(password, user['password_hash']), 401, 'unauthenticated')
            token = secrets.token_urlsafe(32)
            state['sessions'][token] = user['id']
            return (201 if path == '/auth/signup' else 200), {
                'user_id': user['id'], 'display_name': user['display_name'], 'token': token}
        if method == 'GET' and path == '/restaurants':
            return 200, {'restaurants': [{k: r[k] for k in ('id', 'name', 'timezone')} for r in state['restaurants']]}
        if method == 'GET' and re.fullmatch(r'/restaurants/[^/]+', path):
            from model import restaurant
            return 200, restaurant(state, path.split('/')[2])
        if method == 'GET' and path == '/availability':
            from model import restaurant
            require(all(k in query for k in ('restaurant_id', 'date', 'party_size')))
            day = local_date(query['date'])
            require(re.fullmatch(r'[0-9]+', query['party_size']) is not None)
            party = integer(int(query['party_size']))
            r = restaurant(state, query['restaurant_id'])
            slots, seen = [], set()
            for hours in r['opening_hours']:
                if hours['weekday'] != DAYS[day.weekday()]:
                    continue
                for minute in range(clock_minutes(hours['opens']), clock_minutes(hours['closes']), r['slot_minutes']):
                    wall = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)
                    local = wall.isoformat(timespec='minutes')
                    if local in seen:
                        continue
                    # Geometry uses any table; capacity and occupancy are separate filters.
                    if not r['tables']:
                        from model import resolve
                        zone = ZoneInfo(r['timezone'])
                        try:
                            start = resolve(wall, zone)
                            end = start.astimezone(UTC) + timedelta(minutes=r['reservation_duration_minutes'])
                            close = datetime.combine(day, datetime.strptime(hours['closes'], '%H:%M').time()).replace(tzinfo=zone)
                            if end > close.astimezone(UTC):
                                continue
                        except (APIError, OverflowError):
                            continue
                        fields = {'starts_at': start.isoformat()}
                    else:
                        try:
                            fields = booking_fields(state, {'restaurant_id': r['id'], 'table_id': r['tables'][0]['id'],
                                                           'party_size': 1, 'starts_at_local': local})
                        except APIError as error:
                            if error.code in ('invalid_local_time', 'outside_opening_hours'):
                                continue
                            raise
                    available = []
                    for table in r['tables']:
                        candidate = {**fields, 'table_id': table['id'], 'status': 'confirmed'}
                        if table['capacity'] >= party and not any(overlap(candidate, b) for b in state['reservations']):
                            available.append(table['id'])
                    slots.append({'starts_at_local': local, 'starts_at': fields['starts_at'], 'available_table_ids': available})
                    seen.add(local)
            return 200, {'restaurant_id': r['id'], 'date': query['date'], 'timezone': r['timezone'], 'slots': slots}

        uid = self.authenticate(headers)
        if method == 'GET' and path == '/reservations':
            records = sorted((r for r in state['reservations'] if r['user_id'] == uid),
                             key=lambda r: instant(r['starts_at']), reverse=True)
            return 200, {'reservations': [public(r) for r in records]}
        if method == 'POST' and path in ('/reservations', '/reservation-moves'):
            replay, key = self.receipt(uid, method, path, headers, body)
            if replay is not None:
                return 200, replay
            if path == '/reservations':
                record = booking_fields(state, body)
                reference = secrets.token_hex(5).upper()
                while any(r['reference'] == reference for r in state['reservations']):
                    reference = secrets.token_hex(5).upper()
                record.update(reservation_id='res_' + uuid.uuid4().hex, reference=reference,
                              user_id=uid, status='confirmed', created_at=datetime.now(UTC).isoformat())
                self.ensure_available([record])
                state['reservations'].append(record)
                response = public(record)
            else:
                moves = body.get('moves')
                require(isinstance(moves, list) and 1 <= len(moves) <= 8)
                require(all(isinstance(m, dict) and isinstance(m.get('reference'), str) for m in moves))
                require(len({m['reference'] for m in moves}) == len(moves))
                replacements, rid = [], None
                for move in moves:
                    record = self.owned(move['reference'], uid)
                    require(rid is None or rid == record['restaurant_id'])
                    rid = record['restaurant_id']
                    replacements.append(self.amendment(record, move))
                self.ensure_available(replacements)
                self.replace(replacements)
                response = {'reservations': [public(r) for r in replacements]}
            state['receipts'].append({'user_id': uid, 'method': method, 'path': path, 'key': key,
                                      'body': copy.deepcopy(body), 'response': copy.deepcopy(response)})
            return 201, response
        match = re.fullmatch(r'/reservations/([^/]+)(/cancel)?', path)
        if match:
            record = self.owned(match[1], uid)
            if method == 'GET' and not match[2]:
                return 200, public(record)
            if method == 'POST' and match[2]:
                if record['status'] != 'cancelled':
                    check_cutoff(state, record)
                    record['status'] = 'cancelled'
                return 200, public(record)
            if method == 'PATCH' and not match[2]:
                replacement = self.amendment(record, body)
                self.ensure_available([replacement])
                self.replace([replacement])
                return 200, public(replacement)
        raise APIError(404, 'not_found')
