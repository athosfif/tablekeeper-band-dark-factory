"""One process, one serializable transaction boundary for all observable state.

Validation builds candidate records before assignment. Readers and snapshots share
the same lock. A successful write and its immutable receipt commit together.
"""
from copy import deepcopy
import re
import secrets
from threading import RLock
from urllib.parse import parse_qs, unquote, urlsplit

from domain import available, changed, check_cutoff, overlaps, proposal, public_record, seating_options
from policies import effective_config, policy_body, selected_terms
from ledger import append_event, bump_restaurant, commit_changes, new_record, public_series
from agreements import adopt, amend
from planning import preview, apply_plan
from security import hash_password, verify_password
from state import empty_state, fixture_state, imported_state, receipt_key
from timekeeping import calendar_date, instant, now, starts
from validation import email, field, identifier, object_body, require


class Application:
    def __init__(self):
        self.lock = RLock()
        self.state = empty_state()

    def handle(self, method, target, headers, body):
        with self.lock:
            status, payload = self.dispatch(method, target, headers, body)
            return status, deepcopy(payload)

    def user(self, headers):
        match = re.fullmatch(r'Bearer ([^\s]+)', headers.get('Authorization', ''), flags=re.IGNORECASE)
        require(match is not None and match[1] in self.state['tokens'], 'unauthenticated', 401)
        return self.state['tokens'][match[1]]

    def owned(self, ref, uid):
        record = self.state['reservations'].get(ref)
        require(record is not None and record['user_id'] == uid, 'not_found', 404)
        return record

    def session(self, user):
        token = secrets.token_urlsafe(32)
        self.state['tokens'][token] = user['id']
        return {k: v for k, v in [('user_id', user['id']), ('display_name', user['display_name']), ('token', token)]}

    def dispatch(self, method, target, headers, body):
        url = urlsplit(target)
        # Split routes before decoding an opaque identifier that may contain '/'.
        path = url.path
        if method == 'GET' and path == '/health':
            return 200, {'status': 'ok'}
        if method == 'POST' and path == '/_test/reset':
            self.state = fixture_state(object_body(body))
            return 204, None
        if method == 'GET' and path == '/_test/export':
            return 200, {'track': 'tablekeeper', 'format_version': 1, 'state': self.state}
        if method == 'POST' and path == '/_test/import':
            self.state = imported_state(object_body(body))
            return 204, None
        if method == 'POST' and path in ('/auth/signup', '/auth/login'):
            object_body(body)
            address, password = email(body), field(body, 'password', str)
            require(len(password) >= 8)
            existing = next((u for u in self.state['users'].values() if u['email'] == address), None)
            if path == '/auth/login':
                require(existing is not None and verify_password(password, existing['password_hash']), 'unauthenticated', 401)
                return 200, self.session(existing)
            name = field(body, 'display_name', str)
            require(existing is None, 'email_taken', 409)
            uid = 'u_' + secrets.token_hex(16)
            user = {'id': uid, 'email': address, 'display_name': name, 'password_hash': hash_password(password)}
            self.state['users'][uid] = user
            return 201, self.session(user)
        if method == 'GET' and path == '/restaurants':
            return 200, {'restaurants': [{k: r[k] for k in ('id', 'name', 'timezone')}
                                         for r in self.state['restaurants'].values()]}
        if method == 'GET' and re.fullmatch(r'/restaurants/[^/]+', path):
            rid = unquote(path.rsplit('/', 1)[1])
            identifier({'id': rid}, 'id')
            require(rid in self.state['restaurants'], 'not_found', 404)
            return 200, self.state['restaurants'][rid]
        policy_route = re.fullmatch(r'/restaurants/([^/]+)/policies', path)
        if method == 'GET' and policy_route:
            rid = identifier({'id': unquote(policy_route[1])}, 'id')
            require(rid in self.state['restaurants'], 'not_found', 404)
            return 200, {'policies': self.state['policies'][rid]}
        if method == 'GET' and path == '/availability':
            query = {k: v[0] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
            require('explain' not in query or query['explain'] == 'true')
            rid = identifier(query, 'restaurant_id')
            day = calendar_date(field(query, 'date', str))
            count = field(query, 'party_size', str)
            require(re.fullmatch(r'[0-9]+', count) is not None)
            size = int(count)
            require(size > 0)
            require(rid in self.state['restaurants'], 'not_found', 404)
            original = self.state['restaurants'][rid]
            terms = selected_terms(original, day.isoformat(), self.state['policies'][rid])
            restaurant = effective_config(original, terms)
            slots = []
            for local, start, end in starts(restaurant, day):
                options = []
                for option in seating_options(restaurant):
                    candidate = {'restaurant_id': rid, 'table_ids': option['table_ids'],
                                 'starts_at': start.isoformat(), 'ends_at': end.isoformat()}
                    if option['capacity'] >= size and available(candidate, self.state['reservations'], closures=self.state['closures'].values()):
                        options.append(option)
                tables = [o['table_ids'][0] for o in options if len(o['table_ids']) == 1]
                slot = {'starts_at_local': local, 'starts_at': start.isoformat(),
                        'available_table_ids': tables, 'available_options': options}
                if 'explain' in query:
                    slot['explain'] = []
                    for table in restaurant['tables']:
                        candidate = {'restaurant_id': rid, 'table_ids': [table['id']],
                                     'starts_at': start.isoformat(), 'ends_at': end.isoformat()}
                        capacity, free = size <= table['capacity'], available(candidate, self.state['reservations'], closures=self.state['closures'].values())
                        slot['explain'].append({'table_id': table['id'], 'policy_version': terms['policy_version'],
                                                'available': capacity and free,
                                                'rules': [{'rule': 'capacity', 'holds': capacity},
                                                          {'rule': 'no_overlap', 'holds': free}]})
                slots.append(slot)
            return 200, {'restaurant_id': rid, 'date': query['date'], 'timezone': restaurant['timezone'], 'slots': slots}

        private_read = re.fullmatch(r'/reservations/([^/]+)/(history|decision)', path)
        series_read = re.fullmatch(r'/series/([^/]+)', path)
        if method == 'GET' and (private_read or series_read):
            from validation import APIError
            try:
                uid = self.user(headers)
            except APIError:
                require(False, 'not_found', 404)
            if private_read:
                record = self.owned(unquote(private_read[1]), uid)
                if private_read[2] == 'history':
                    return 200, {'reference': record['reference'], 'entries': self.state['histories'][record['reference']]}
                return 200, {k: record[k] for k in ('reference', 'revision', 'accepted_terms')}
            series = self.state['series'].get(unquote(series_read[1]))
            require(series is not None and series['user_id'] == uid, 'not_found', 404)
            return 200, public_series(series, self.state)
        replan_route = re.fullmatch(r'/restaurants/([^/]+)/replans(?:/([^/]+)/apply)?', path)
        amend_route = re.fullmatch(r'/series/([^/]+)/amend', path)
        uid = self.user(headers)
        if method in ('POST', 'PATCH'):
            object_body(body)
        if method == 'POST' and (path in ('/reservations', '/reservation-moves', '/series') or policy_route or replan_route or amend_route):
            key = headers.get('Idempotency-Key', '')
            require(bool(key), 'missing_idempotency_key', 400)
            require(len(key) <= 255)
            namespace = receipt_key(uid, path, key)
            receipt = self.state['receipts'].get(namespace)
            if receipt is not None:
                from validation import same_json
                require(same_json(body, receipt['body']), 'idempotency_key_reuse', 409)
                return 200, receipt['response']
            if path == '/reservations':
                response = self.create(uid, body)
            elif path == '/reservation-moves':
                response = self.move(uid, body)
            elif path == '/series':
                response = adopt(self.state, uid, body)
            elif amend_route:
                response = amend(self.state, uid, unquote(amend_route[1]), body)
            else:
                manager_route = policy_route or replan_route
                rid = identifier({'id': unquote(manager_route[1])}, 'id')
                require(rid in self.state['restaurants'], 'not_found', 404)
                restaurant = self.state['restaurants'][rid]
                require(uid in restaurant['manager_user_ids'], 'forbidden', 403)
                if replan_route:
                    response = (apply_plan(self.state, rid, unquote(replan_route[2])) if replan_route[2]
                                else preview(self.state, rid, body))
                else:
                    response = {**policy_body(body, restaurant), 'policy_version': len(self.state['policies'][rid]) + 1}
                    self.state['policies'][rid].append(response)
                    bump_restaurant(self.state, rid)
            self.state['receipts'][namespace] = {'body': deepcopy(body), 'response': deepcopy(response)}
            return 201, response
        if method == 'GET' and path == '/reservations':
            records = [public_record(r) for r in self.state['reservations'].values() if r['user_id'] == uid]
            records.sort(key=lambda r: instant(r['starts_at']), reverse=True)
            return 200, {'reservations': records}
        match = re.fullmatch(r'/reservations/([^/]+)(/cancel)?', path)
        if match:
            record = self.owned(unquote(match[1]), uid)
            if method == 'GET' and not match[2]:
                return 200, public_record(record)
            if method == 'POST' and match[2]:
                if record['status'] != 'cancelled':
                    check_cutoff(record)
                    record = {**record, 'status': 'cancelled', 'revision': record['revision'] + 1}
                    commit_changes(self.state, [record], 'cancelled')
                return 200, public_record(record)
            if method == 'PATCH' and not match[2]:
                candidate = changed(record, body, self.state['restaurants'], self.state['policies'])
                require(available(candidate, self.state['reservations'], {record['reference']}, self.state['closures'].values()), 'table_unavailable', 409)
                commit_changes(self.state, [candidate])
                return 200, public_record(candidate)
        require(False, 'not_found', 404)

    def create(self, uid, body):
        candidate = proposal(self.state['restaurants'], body, self.state['policies'])
        require(available(candidate, self.state['reservations'], closures=self.state['closures'].values()), 'table_unavailable', 409)
        record = new_record(candidate, uid, self.state['reservations'])
        self.state['reservations'][record['reference']] = record
        append_event(self.state, record, 'created')
        bump_restaurant(self.state, record['restaurant_id'])
        return public_record(record)

    def move(self, uid, body):
        moves = body.get('moves')
        require(type(moves) is list and 1 <= len(moves) <= 8)
        require(all(type(m) is dict and type(m.get('reference')) is str for m in moves))
        refs = [m['reference'] for m in moves]
        require(len(set(refs)) == len(refs))
        candidates = []
        for move in moves:
            current = self.owned(move['reference'], uid)
            if candidates:
                require(current['restaurant_id'] == candidates[0]['restaurant_id'])
            candidates.append(changed(current, move, self.state['restaurants'], self.state['policies']))
        # Only the final complete arrangement participates in occupancy checking.
        for i, candidate in enumerate(candidates):
            require(available(candidate, self.state['reservations'], set(refs), self.state['closures'].values()), 'table_unavailable', 409)
            require(all(not overlaps(candidate, other) for other in candidates[:i]), 'table_unavailable', 409)
        commit_changes(self.state, candidates)
        return {'reservations': [public_record(c) for c in candidates]}
