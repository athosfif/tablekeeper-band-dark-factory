"""One lock is the transaction boundary for reads, writes, snapshots and receipts."""

import re
import secrets
import threading
import uuid
from datetime import datetime, timedelta
from urllib.parse import unquote
from zoneinfo import ZoneInfo

from json_values import clone, dumps

from model import (APIError, DAYS, UTC, booking_fields, check_cutoff, clock_minutes, email,
                   empty_state, field, fixture_state, identifier, imported_state, instant,
                   integer, json_equal, local_date, overlap, password_hash, password_matches,
                   public, require, selected_tables, selection_fields, selection, restaurant,
                   selected_policy, rules_restaurant, policy_body, changes_between, history_event,
                   closure_interval, closure_overlap, solve, time_overlap, plan_response)


class Engine:
    def __init__(self):
        self.state = empty_state()
        self.lock = threading.RLock()

    def handle(self, method, path, query, headers, body):
        with self.lock:
            committed = self.state
            try:
                if method != 'GET':
                    # Work on a detached candidate, including receipts. No mutation
                    # becomes visible unless dispatch AND response encoding succeed.
                    self.state = clone(committed)
                status, value = self.dispatch(method, path, query, headers, body)
                payload = b'' if status == 204 else dumps(value).encode('utf-8')
            except Exception:
                self.state = committed
                raise
            return status, payload

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
        if 'expected_revision' in changes:
            expected = integer(changes['expected_revision'])
            require(expected == record['revision'], 409, 'stale_revision')
        require(record['status'] != 'cancelled', 409, 'reservation_cancelled')
        check_cutoff(self.state, record)
        merged = {k: changes.get(k, record[k]) for k in ('starts_at_local', 'party_size')}
        if 'table_id' in changes or 'table_ids' in changes:
            merged.update({k: changes[k] for k in ('table_id', 'table_ids') if k in changes})
        else:
            merged['table_ids'] = selected_tables(record)
        merged['restaurant_id'] = record['restaurant_id']
        # Establish a real field change before selecting a newer policy: a no-op
        # keeps the booking's accepted terms even after those rules are superseded.
        ids = selection(restaurant(self.state, record['restaurant_id']), merged)
        if (ids == selected_tables(record) and
                json_equal(merged['starts_at_local'], record['starts_at_local']) and
                type(merged['party_size']) in (int, float) and
                merged['party_size'] == record['party_size']):
            return record
        fields = booking_fields(self.state, merged)
        return {**{k: v for k, v in record.items() if k not in ('table_id', 'table_ids')},
                **fields, 'revision': record['revision'] + 1}

    def bump(self, rid):
        self.state['restaurant_revisions'][rid] += 1

    def series_for(self, reference):
        for series in self.state['series']:
            for item in series['occurrences']:
                if item['reference'] == reference:
                    return series, item
        return None, None

    def commit_amendments(self, replacements, exceptions=True):
        changed_restaurants, changed_series = set(), set()
        originals = {r['reservation_id']: r for r in self.state['reservations']}
        for record in replacements:
            old = originals[record['reservation_id']]
            if old['revision'] == record['revision']:
                continue
            history_event(self.state, record, 'changed', changes_between(old, record))
            changed_restaurants.add(record['restaurant_id'])
            series, item = self.series_for(record['reference'])
            if series:
                changed_series.add(series['series_id'])
                if exceptions:
                    item['exception'] = True
        self.replace(replacements)
        for rid in changed_restaurants:
            self.bump(rid)
        for series in self.state['series']:
            if series['series_id'] in changed_series:
                series['revision'] += 1

    def new_reservation(self, uid, body):
        record = booking_fields(self.state, body)
        reference = secrets.token_hex(5).upper()
        while any(r['reference'] == reference for r in self.state['reservations']):
            reference = secrets.token_hex(5).upper()
        record.update(reservation_id='res_' + uuid.uuid4().hex, reference=reference,
                      user_id=uid, status='confirmed', revision=1, created_at=datetime.now(UTC).isoformat())
        self.ensure_available([record])
        self.state['reservations'].append(record)
        history_event(self.state, record, 'created', changes_between(None, record), record['created_at'])
        return record

    def series_response(self, series):
        return {k: clone(series[k]) for k in ('series_id', 'revision', 'interval_weeks')} | {
            'occurrences': [{k: clone(item[k]) for k in ('index', 'reference', 'exception')} | {
                'reservation': public(self.owned(item['reference'], series['user_id']))}
                for item in series['occurrences']]}

    def save_receipt(self, uid, method, path, key, body, response):
        self.state['receipts'].append({'user_id': uid, 'method': method, 'path': path, 'key': key,
                                      'body': clone(body), 'response': clone(response)})

    def ensure_available(self, replacements):
        ids = {r['reservation_id'] for r in replacements}
        unlisted = [r for r in self.state['reservations'] if r['reservation_id'] not in ids]
        for i, record in enumerate(replacements):
            require(not any(overlap(record, r) for r in unlisted + replacements[i + 1:]),
                    409, 'table_unavailable')
            require(not any(closure_overlap(record, c) for c in self.state['closures']),
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
        policy_match = re.fullmatch(r'/restaurants/([^/]+)/policies', path)
        if policy_match and method == 'GET':
            r = restaurant(state, unquote(policy_match[1]))
            return 200, {'policies': state['policies'][r['id']]}
        if method == 'GET' and re.fullmatch(r'/restaurants/[^/]+', path):
            # Split the encoded route first: an encoded slash belongs to the
            # opaque ID, not to the routing structure. Decode that ID once only.
            return 200, restaurant(state, unquote(path.split('/')[2]))
        if method == 'GET' and path == '/availability':
            require(all(k in query for k in ('restaurant_id', 'date', 'party_size')))
            day = local_date(query['date'])
            require(re.fullmatch(r'[0-9]+', query['party_size']) is not None)
            party = integer(int(query['party_size']))
            require('explain' not in query or query['explain'] == 'true')
            r = restaurant(state, query['restaurant_id'])
            terms = selected_policy(state, r, query['date'])
            r = rules_restaurant(r, terms)
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
                    available, options, explanations = [], [], []
                    for ids in [[t['id']] for t in r['tables']] + r.get('combinable', []):
                        capacity = sum(t['capacity'] for t in r['tables'] if t['id'] in ids)
                        candidate = {**fields, 'restaurant_id': r['id'], 'table_ids': ids, 'status': 'confirmed'}
                        free = (not any(overlap(candidate, b) for b in state['reservations'])
                                and not any(closure_overlap(candidate, c) for c in state['closures']))
                        if len(ids) == 1:
                            explanations.append({'table_id': ids[0], 'policy_version': terms['policy_version'],
                                                 'available': capacity >= party and free,
                                                 'rules': [{'rule': 'capacity', 'holds': capacity >= party},
                                                           {'rule': 'no_overlap', 'holds': free}]})
                        if capacity >= party and free:
                            options.append({'table_ids': list(ids), 'capacity': capacity})
                            if len(ids) == 1:
                                available.append(ids[0])
                    slots.append({'starts_at_local': local, 'starts_at': fields['starts_at'],
                                  'available_table_ids': available, 'available_options': options,
                                  **({'explain': explanations} if 'explain' in query else {})})
                    seen.add(local)
            return 200, {'restaurant_id': r['id'], 'date': query['date'], 'timezone': r['timezone'], 'slots': slots}

        private_read = (method == 'GET' and (re.fullmatch(r'/reservations/[^/]+/(history|decision)', path)
                                             or re.fullmatch(r'/series/[^/]+', path)))
        try:
            uid = self.authenticate(headers)
        except APIError:
            if private_read:
                raise APIError(404, 'not_found') from None
            raise
        replan_match = re.fullmatch(r'/restaurants/([^/]+)/replans(?:/([^/]+)/apply)?', path)
        amend_match = re.fullmatch(r'/series/([^/]+)/amend', path)
        if method == 'POST' and (replan_match or amend_match):
            replay, key = self.receipt(uid, method, path, headers, body)
            if replay is not None:
                return 200, replay
            if replan_match:
                r = restaurant(state, unquote(replan_match[1]))
                require(uid in r.get('manager_user_ids', []), 403, 'forbidden')
                if replan_match[2] is None:
                    tid = identifier(field(body, 'table_id'))
                    require(any(t['id'] == tid for t in r['tables']), 404, 'not_found')
                    closure = closure_interval(body)
                    current = [b for b in state['reservations'] if b['restaurant_id'] == r['id'] and b['status'] == 'confirmed']
                    considered, fixed = [], []
                    for b in current:
                        intersects = time_overlap(instant(b['starts_at']), instant(b['ends_at']),
                                                  instant(closure['from']), instant(closure['to']))
                        (considered if intersects else fixed).append(public(b))
                    considered.sort(key=lambda b:b['reference'])
                    closures = [clone(c) for c in state['closures'] if c['restaurant_id'] == r['id']]
                    result = solve(r, closure, considered, fixed, closures)
                    plan = {'plan_id': 'plan_' + uuid.uuid4().hex, 'restaurant_id': r['id'], 'user_id': uid,
                            'restaurant_revision': state['restaurant_revisions'][r['id']], 'closure': closure,
                            **result, 'applied': False, 'basis': {'considered': considered, 'fixed': fixed, 'closures': closures}}
                    state['plans'].append(plan)
                    response = plan_response(plan)
                else:
                    plan = next((p for p in state['plans'] if p['plan_id'] == unquote(replan_match[2])
                                 and p['restaurant_id'] == r['id']), None)
                    require(plan is not None, 404, 'not_found')
                    require(not plan['applied'], 409, 'plan_already_applied')
                    require(plan['restaurant_revision'] == state['restaurant_revisions'][r['id']], 409, 'stale_plan')
                    changed_series, records = set(), []
                    for assignment in plan['assignments']:
                        record = next(b for b in state['reservations'] if b['reference'] == assignment['reference'])
                        if assignment['changed']:
                            old_ids = selected_tables(record)
                            record.pop('table_id', None)
                            record.update(selection_fields(assignment['table_ids']))
                            record['revision'] += 1
                            history_event(state, record, 'reassigned', [{'field':'table_ids','from':old_ids,'to':record['table_ids']}],
                                          plan_id=plan['plan_id'])
                            series, _ = self.series_for(record['reference'])
                            if series:
                                changed_series.add(series['series_id'])
                        records.append(public(record))
                    for series in state['series']:
                        if series['series_id'] in changed_series:
                            series['revision'] += 1
                    state['closures'].append({**clone(plan['closure']), 'restaurant_id': r['id'], 'plan_id': plan['plan_id']})
                    plan['applied'] = True
                    self.bump(r['id'])
                    response = {'plan_id':plan['plan_id'], 'restaurant_revision':state['restaurant_revisions'][r['id']],
                                'reservations':records}
            else:
                series = next((s for s in state['series'] if s['series_id'] == unquote(amend_match[1]) and s['user_id'] == uid), None)
                require(series is not None, 404, 'not_found')
                try:
                    expected = integer(body['expected_revision'])
                    start_index = integer(body['from_index'],0)
                    require(start_index < len(series['occurrences']))
                    clock_minutes(body['local_time'])
                except (APIError, KeyError, TypeError, ValueError):
                    raise APIError(message='Invalid series amendment') from None
                require(expected == series['revision'], 409, 'stale_revision')
                replacements = []
                for item in series['occurrences'][start_index:]:
                    record = self.owned(item['reference'], uid)
                    if item['exception'] or record['status'] == 'cancelled':
                        continue
                    local = item['scheduled_date'] + 'T' + body['local_time']
                    replacements.append(record if local == record['starts_at_local'] else
                                        self.amendment(record, {'starts_at_local':local}))
                self.ensure_available(replacements)
                self.commit_amendments(replacements, exceptions=False)
                response = self.series_response(series)
            self.save_receipt(uid, method, path, key, body, response)
            return 201, response
        if private_read:
            history_match = re.fullmatch(r'/reservations/([^/]+)/(history|decision)', path)
            if history_match:
                record = self.owned(unquote(history_match[1]), uid)
                if history_match[2] == 'history':
                    return 200, {'reference': record['reference'], 'entries': state['histories'][record['reference']]}
                return 200, {k: clone(record[k]) for k in ('reference', 'revision', 'accepted_terms')}
            series = next((s for s in state['series'] if s['series_id'] == unquote(path.split('/')[2])
                           and s['user_id'] == uid), None)
            require(series is not None, 404, 'not_found')
            return 200, self.series_response(series)
        if method == 'POST' and (policy_match or path == '/series'):
            replay, key = self.receipt(uid, method, path, headers, body)
            if replay is not None:
                return 200, replay
            if policy_match:
                r = restaurant(state, unquote(policy_match[1]))
                require(uid in r.get('manager_user_ids', []), 403, 'forbidden')
                response = {**policy_body(r, body), 'policy_version': len(state['policies'][r['id']]) + 1}
                state['policies'][r['id']].append(clone(response))
                self.bump(r['id'])
            else:
                anchor = self.owned(field(body, 'anchor_reference'), uid)
                require(anchor['status'] != 'cancelled', 409, 'reservation_cancelled')
                require(self.series_for(anchor['reference'])[0] is None, 409, 'already_in_series')
                check_cutoff(state, anchor)
                count, interval = integer(body.get('count')), integer(body.get('interval_weeks'))
                require(2 <= count <= 12 and 1 <= interval <= 4)
                day = local_date(anchor['starts_at_local'][:10])
                series = {'series_id': 'ser_' + uuid.uuid4().hex, 'user_id': uid,
                          'restaurant_id': anchor['restaurant_id'], 'revision': 1,
                          'interval_weeks': interval, 'occurrences': []}
                for index in range(count):
                    scheduled = (day + timedelta(weeks=index * interval)).isoformat()
                    record = anchor if index == 0 else self.new_reservation(uid, {
                        'restaurant_id': anchor['restaurant_id'], 'table_ids': selected_tables(anchor),
                        'party_size': anchor['party_size'],
                        'starts_at_local': scheduled + anchor['starts_at_local'][10:]})
                    series['occurrences'].append({'index': index, 'reference': record['reference'],
                                                  'exception': False, 'scheduled_date': scheduled})
                state['series'].append(series)
                self.bump(anchor['restaurant_id'])
                response = self.series_response(series)
            self.save_receipt(uid, method, path, key, body, response)
            return 201, response
        if method == 'GET' and path == '/reservations':
            records = sorted((r for r in state['reservations'] if r['user_id'] == uid),
                             key=lambda r: instant(r['starts_at']), reverse=True)
            return 200, {'reservations': [public(r) for r in records]}
        if method == 'POST' and path in ('/reservations', '/reservation-moves'):
            replay, key = self.receipt(uid, method, path, headers, body)
            if replay is not None:
                return 200, replay
            if path == '/reservations':
                record = self.new_reservation(uid, body)
                self.bump(record['restaurant_id'])
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
                self.commit_amendments(replacements)
                response = {'reservations': [public(r) for r in replacements]}
            self.save_receipt(uid, method, path, key, body, response)
            return 201, response
        match = re.fullmatch(r'/reservations/([^/]+)(/cancel)?', path)
        if match:
            record = self.owned(unquote(match[1]), uid)
            if method == 'GET' and not match[2]:
                return 200, public(record)
            if method == 'POST' and match[2]:
                if record['status'] != 'cancelled':
                    check_cutoff(state, record)
                    record['status'] = 'cancelled'
                    record['revision'] += 1
                    history_event(state, record, 'cancelled', [])
                    self.bump(record['restaurant_id'])
                    series, _ = self.series_for(record['reference'])
                    if series:
                        series['revision'] += 1
                return 200, public(record)
            if method == 'PATCH' and not match[2]:
                replacement = self.amendment(record, body)
                self.ensure_available([replacement])
                self.commit_amendments([replacement])
                return 200, public(replacement)
        raise APIError(404, 'not_found')
