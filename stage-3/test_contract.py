"""Builder's specification-derived HTTP checks; no official tests are imported.

Run: python -m unittest -v test_contract
Set TABLEKEEPER_URL and TABLEKEEPER_SECOND_URL to test two running containers.
Without them, this module starts two independent local server subprocesses.
No snapshots, passwords or session tokens are printed or saved.
"""

import copy
import json
import os
import socket
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def fixture(zone='Europe/Berlin', opening='18:00', closing='23:00', duration=90):
    return {'users': [{'id': 'ada', 'email': 'ada@example.test', 'password': 'fixture-pass', 'display_name': 'Ada'},
                      {'id': 'bob', 'email': 'bob@example.test', 'password': 'fixture-pass', 'display_name': 'Bob'}],
            'restaurants': [{'id': 'r', 'name': 'Test Restaurant', 'timezone': zone, 'slot_minutes': 30,
                             'reservation_duration_minutes': duration, 'cancellation_cutoff_minutes': 120,
                             'opening_hours': [{'weekday': d, 'opens': opening, 'closes': closing}
                                               for d in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']],
                             'tables': [{'id': f't{i}', 'label': str(i), 'capacity': i * 2} for i in range(1, 5)]}],
            'reservations': []}


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.children = []
        cls.urls = []
        for key in ['TABLEKEEPER_URL', 'TABLEKEEPER_SECOND_URL']:
            if os.environ.get(key):
                cls.urls.append(os.environ[key].rstrip('/'))
                continue
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            child = subprocess.Popen([sys.executable, 'server.py'], cwd=Path(__file__).parent,
                                     env={**os.environ, 'PORT': str(port), 'PYTHONDONTWRITEBYTECODE': '1'},
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cls.children.append(child)
            base = f'http://127.0.0.1:{port}'
            cls.urls.append(base)
            for _ in range(200):
                try:
                    with urlopen(base + '/health', timeout=.5) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(.025)
            else:
                raise RuntimeError('Server startup failed')
        cls.durations = []

    @classmethod
    def tearDownClass(cls):
        for child in cls.children:
            child.terminate()
            child.wait(timeout=5)
        print(f'HTTP requests: {len(cls.durations)}; slowest: {max(cls.durations):.4f}s')

    def request(self, method, path, body=None, token=None, key=None, server=0, raw=None):
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        if token is not None:
            headers['Authorization'] = 'Bearer ' + token
        if key is not None:
            headers['Idempotency-Key'] = key
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        started = time.monotonic()
        try:
            response = urlopen(Request(self.urls[server] + path, data=data, headers=headers, method=method), timeout=5)
        except HTTPError as error:
            response = error
        with response:
            payload = response.read()
            value = json.loads(payload) if payload else None
            status = response.status
            self.assertTrue('application/json' in response.headers.get('Content-Type', ''))
        self.durations.append(time.monotonic() - started)
        self.assertLess(status, 500)
        return status, value

    def setUp(self):
        self.assertEqual(self.request('POST', '/_test/reset', fixture())[0], 204)
        self.ada = self.login('ada')
        self.bob = self.login('bob')

    def login(self, name, server=0):
        status, body = self.request('POST', '/auth/login', {'email': f'{name}@example.test', 'password': 'fixture-pass'}, server=server)
        self.assertEqual(status, 200)
        return body['token']

    def booking(self, **changes):
        return {'restaurant_id': 'r', 'table_id': 't1', 'party_size': 2,
                'starts_at_local': '2032-10-25T19:00', **changes}

    def create(self, key='new', **changes):
        status, body = self.request('POST', '/reservations', self.booking(**changes), self.ada, key)
        self.assertEqual(status, 201)
        return body

    def error(self, result, status, code):
        self.assertEqual(result[0], status)
        self.assertEqual(result[1].get('error', {}).get('code'), code)

    def snapshot(self, server=0):
        return self.request('GET', '/_test/export', server=server)[1]

    def test_public_auth_sessions_privacy(self):
        for path in ['/health', '/restaurants', '/restaurants/r', '/availability?restaurant_id=r&date=2032-10-25&party_size=2']:
            self.assertEqual(self.request('GET', path)[0], 200)
        self.error(self.request('GET', '/reservations'), 401, 'unauthenticated')
        self.error(self.request('GET', '/reservations', token='unknown'), 401, 'unauthenticated')
        again = self.login('ada')
        self.assertNotEqual(again, self.ada)
        for token in [again, self.ada]:
            self.assertEqual(self.request('GET', '/reservations', token=token), (200, {'reservations': []}))
        record = self.create()
        self.error(self.request('GET', '/reservations/' + record['reference'], token=self.bob), 404, 'not_found')
        self.error(self.request('POST', '/reservations/' + record['reference'] + '/cancel', {}, self.bob), 404, 'not_found')
        self.assertTrue(all('password' not in u and 'scrypt$' in u['password_hash'] for u in self.snapshot()['state']['users']))

    def test_signup_validation_and_login(self):
        body = {'email': 'new@example.test', 'password': 'new-password', 'display_name': 'New'}
        self.assertEqual(self.request('POST', '/auth/signup', body)[0], 201)
        self.error(self.request('POST', '/auth/signup', body), 409, 'email_taken')
        for patch in [{'email': 'bad'}, {'password': 'short'}]:
            self.error(self.request('POST', '/auth/signup', {**body, **patch}), 422, 'validation_failed')
        self.error(self.request('POST', '/auth/login', {**body, 'password': 'wrong'}), 401, 'unauthenticated')
        self.error(self.request('POST', '/auth/signup', {**body, 'display_name': 9}), 400, 'malformed_request')

    def test_errors_types_keys_and_queries(self):
        for raw in [b'{', b'[]', b'null', b'{"x":NaN}', b'{"x":1e999}']:
            self.error(self.request('POST', '/reservations', token=self.ada, key='bad', raw=raw), 400, 'malformed_request')
        for key in [None, '']:
            self.error(self.request('POST', '/reservations', self.booking(), self.ada, key), 400, 'missing_idempotency_key')
        self.error(self.request('POST', '/reservations', self.booking(), self.ada, 'x' * 256), 422, 'validation_failed')
        for value in [True, False, '2', 0, -1, 2.5, None]:
            self.error(self.request('POST', '/reservations', self.booking(party_size=value), self.ada, 'retry'), 422, 'validation_failed')
        for value in [False, [], 7]:
            self.error(self.request('POST', '/reservations', self.booking(table_id=value), self.ada, 'retry'), 400, 'malformed_request')
        for value in ['2032-10-25T19:00Z', '2032-10-25T19:00:00', '2032-10-25T19:00+01:00', '2032-02-30T19:00']:
            self.error(self.request('POST', '/reservations', self.booking(starts_at_local=value), self.ada, 'retry'), 422, 'validation_failed')
        for value in ['1e9', '4.0', '+4', '-1', '0']:
            query = urlencode({'restaurant_id': 'r', 'date': '2032-10-25', 'party_size': value})
            self.error(self.request('GET', '/availability?' + query), 422, 'validation_failed')
        self.create('retry')

    def test_idempotency_full_body_and_replay_precedence(self):
        body = self.booking(extra={'number': 1, 'flags': [True, None]})
        original = self.request('POST', '/reservations', body, self.ada, 'scope')
        self.assertEqual(original[0], 201)
        self.assertEqual(self.request('POST', '/reservations', dict(reversed(list(body.items()))), self.ada, 'scope'), (200, original[1]))
        numeric = copy.deepcopy(body)
        numeric['extra']['number'] = 1.0
        self.assertEqual(self.request('POST', '/reservations', numeric, self.ada, 'scope'), (200, original[1]))
        for bad in [{}, {**body, 'restaurant_id': 'missing'}, {**body, 'extra': {'number': True, 'flags': [True, None]}}]:
            self.error(self.request('POST', '/reservations', bad, self.ada, 'scope'), 409, 'idempotency_key_reuse')
        reference = original[1]['reference']
        self.assertEqual(self.request('POST', f'/reservations/{reference}/cancel', {}, self.ada)[0], 200)
        self.assertEqual(self.request('POST', '/reservations', body, self.ada, 'scope'), (200, original[1]))
        self.assertEqual(self.request('POST', '/reservations', body, self.bob, 'scope')[0], 201)
        self.error(self.request('POST', '/reservation-moves', {'moves': [{'reference': reference}]}, self.ada, 'scope'), 409, 'reservation_cancelled')

    def test_capacity_grid_and_past_dates(self):
        for patch, code, status in [({'party_size': 3}, 'party_exceeds_capacity', 422),
                                    ({'starts_at_local': '2032-10-25T19:10'}, 'not_on_slot_grid', 422),
                                    ({'starts_at_local': '2032-10-25T17:00'}, 'outside_opening_hours', 422),
                                    ({'starts_at_local': '2032-10-25T22:00'}, 'outside_opening_hours', 422),
                                    ({'table_id': 'none'}, 'not_found', 404)]:
            self.error(self.request('POST', '/reservations', self.booking(**patch), self.ada, 'failed'), status, code)
        record = self.create('failed', starts_at_local='2020-01-01T19:00')
        self.error(self.request('POST', f'/reservations/{record["reference"]}/cancel', {}, self.ada), 409, 'cutoff_passed')
        self.error(self.request('PATCH', f'/reservations/{record["reference"]}', {'starts_at_local': '2032-10-25T19:00'}, self.ada), 409, 'cutoff_passed')

    def test_half_open_availability_cancel_and_list(self):
        first = self.create()
        self.create('adjacent', starts_at_local='2032-10-25T20:30')
        self.error(self.request('POST', '/reservations', self.booking(starts_at_local='2032-10-25T20:00'), self.ada, 'overlap'), 409, 'table_unavailable')
        availability = self.request('GET', '/availability?restaurant_id=r&date=2032-10-25&party_size=2')[1]
        slot = next(s for s in availability['slots'] if s['starts_at_local'].endswith('19:00'))
        self.assertEqual(slot['available_table_ids'], ['t2', 't3', 't4'])
        for _ in range(2):
            self.assertEqual(self.request('POST', f'/reservations/{first["reference"]}/cancel', {}, self.ada)[0], 200)
        availability = self.request('GET', '/availability?restaurant_id=r&date=2032-10-25&party_size=2')[1]
        self.assertEqual(next(s for s in availability['slots'] if s['starts_at_local'].endswith('19:00'))['available_table_ids'], ['t1', 't2', 't3', 't4'])
        listed = self.request('GET', '/reservations', token=self.ada)[1]['reservations']
        self.assertEqual([r['status'] for r in listed], ['confirmed', 'cancelled'])

    def test_patch_noop_and_atomic_failure(self):
        a, b = self.create(), self.create('second', table_id='t2')
        self.assertEqual(self.request('PATCH', f'/reservations/{a["reference"]}', {'ignored': 7}, self.ada), (200, a))
        before = self.snapshot()
        self.error(self.request('PATCH', f'/reservations/{a["reference"]}', {'table_id': 't2'}, self.ada), 409, 'table_unavailable')
        self.assertTrue(before == self.snapshot(), 'failed patch changed state')
        status, changed = self.request('PATCH', f'/reservations/{a["reference"]}', {'table_id': 't3', 'party_size': 5}, self.ada)
        self.assertEqual(status, 200)
        for key in ['reference', 'reservation_id', 'created_at']:
            self.assertEqual(changed[key], a[key])
        self.assertEqual(self.request('POST', '/reservations', self.booking(), self.ada, 'new'), (200, a))

    def test_batch_cycles_noops_and_receipts(self):
        records = [self.create(str(i), table_id=f't{i}') for i in [1, 2, 3]]
        moves = {'moves': [{'reference': r['reference'], 'table_id': f't{(i + 1) % 3 + 1}'} for i, r in enumerate(records)]}
        status, moved = self.request('POST', '/reservation-moves', moves, self.ada, '1')
        self.assertEqual(status, 201)
        self.assertEqual([r['table_id'] for r in moved['reservations']], ['t2', 't3', 't1'])
        noop = {'moves': [{'reference': r['reference']} for r in records]}
        self.assertEqual(self.request('POST', '/reservation-moves', noop, self.ada, 'noop'), (201, moved))
        self.assertEqual(self.request('POST', f'/reservations/{records[0]["reference"]}/cancel', {}, self.ada)[0], 200)
        self.assertEqual(self.request('POST', '/reservation-moves', moves, self.ada, '1'), (200, moved))
        self.error(self.request('POST', '/reservation-moves', {'moves': None}, self.ada, '1'), 409, 'idempotency_key_reuse')

    def test_batch_validation_precedence_and_rollback(self):
        a, b = self.create(), self.create('second', table_id='t2')
        before = self.snapshot()
        for moves in [[], None, [None], [{'reference': a['reference']}] * 2, [{'reference': True}], [{}]]:
            self.error(self.request('POST', '/reservation-moves', {'moves': moves}, self.ada, 'failed'), 422, 'validation_failed')
        conflicting_then_invalid = {'moves': [{'reference': a['reference'], 'table_id': 't2'}, {'reference': b['reference'], 'party_size': False}]}
        self.error(self.request('POST', '/reservation-moves', conflicting_then_invalid, self.ada, 'failed'), 422, 'validation_failed')
        noop_occupancy = {'moves': [{'reference': a['reference'], 'table_id': 't2'}, {'reference': b['reference']}]}
        self.error(self.request('POST', '/reservation-moves', noop_occupancy, self.ada, 'failed'), 409, 'table_unavailable')
        self.assertTrue(before == self.snapshot(), 'failed batches changed state')
        swap = {'moves': [{'reference': a['reference'], 'table_id': 't2'}, {'reference': b['reference'], 'table_id': 't1'}]}
        self.assertEqual(self.request('POST', '/reservation-moves', swap, self.ada, 'failed')[0], 201)

    def test_50_identical_and_conflicting_creates(self):
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lambda _: self.request('POST', '/reservations', self.booking(), self.ada, 'parallel'), range(50)))
        self.assertEqual([s for s, _ in results].count(201), 1)
        self.assertEqual([s for s, _ in results].count(200), 49)
        self.assertTrue(all(b == results[0][1] for _, b in results))
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lambda n: self.request('POST', '/reservations', self.booking(table_id='t2'), self.ada, f'conflict{n}'), range(50)))
        self.assertEqual([s for s, _ in results].count(201), 1)
        self.assertEqual([s for s, _ in results].count(409), 49)

    def test_50_identical_moves(self):
        record = self.create()
        moves = {'moves': [{'reference': record['reference'], 'table_id': 't2'}]}
        with ThreadPoolExecutor(max_workers=50) as pool:
            results = list(pool.map(lambda _: self.request('POST', '/reservation-moves', moves, self.ada, 'parallel'), range(50)))
        self.assertEqual([s for s, _ in results].count(201), 1)
        self.assertEqual([s for s, _ in results].count(200), 49)
        self.assertTrue(all(b == results[0][1] for _, b in results))

    def test_50_logins_stay_within_deadline(self):
        with ThreadPoolExecutor(max_workers=50) as pool:
            tokens = list(pool.map(lambda _: self.login('ada'), range(50)))
        self.assertEqual(len(set(tokens)), 50)

    def test_dst_gaps_first_folds_absolute_duration(self):
        for zone, spring, fall, repeated, offset in [
            ('Europe/Berlin', '2026-03-29', '2026-10-25', '02:00', '+02:00'),
            ('America/New_York', '2026-03-08', '2026-11-01', '01:00', '-04:00')]:
            self.assertEqual(self.request('POST', '/_test/reset', fixture(zone, '00:00', '05:00'))[0], 204)
            self.ada = self.login('ada')
            slots = self.request('GET', f'/availability?restaurant_id=r&date={spring}&party_size=2')[1]['slots']
            self.assertFalse(any(s['starts_at_local'][11:13] == '02' for s in slots))
            self.error(self.request('POST', '/reservations', self.booking(starts_at_local=spring + 'T02:00'), self.ada, 'gap'), 422, 'invalid_local_time')
            record = self.create('fold', starts_at_local=fall + 'T' + repeated)
            self.assertTrue(record['starts_at'].endswith(offset))
            duration = (datetime.fromisoformat(record['ends_at']).astimezone(timezone.utc) - datetime.fromisoformat(record['starts_at']).astimezone(timezone.utc)).total_seconds()
            self.assertEqual(duration, 5400)
            slots = self.request('GET', f'/availability?restaurant_id=r&date={fall}&party_size=2')[1]['slots']
            self.assertEqual(sum(s['starts_at_local'] == fall + 'T' + repeated for s in slots), 1)

    def test_export_import_independent_process_and_replacement(self):
        record = self.create()
        moves = {'moves': [{'reference': record['reference'], 'table_id': 't2'}]}
        moved = self.request('POST', '/reservation-moves', moves, self.ada, 'move')[1]
        self.request('POST', f'/reservations/{record["reference"]}/cancel', {}, self.ada)
        snapshot = self.snapshot()
        self.create('after-snapshot', table_id='t3')
        self.assertEqual(self.request('POST', '/_test/reset', fixture(), server=1)[0], 204)
        discarded = self.login('bob', server=1)
        for _ in range(2):
            self.assertEqual(self.request('POST', '/_test/import', snapshot, server=1)[0], 204)
            self.assertTrue(snapshot == self.snapshot(server=1), 'import changed snapshot')
            self.error(self.request('GET', '/reservations', token=discarded, server=1), 401, 'unauthenticated')
            self.assertEqual(self.request('POST', '/reservations', self.booking(), self.ada, 'new', server=1), (200, record))
            self.assertEqual(self.request('POST', '/reservation-moves', moves, self.ada, 'move', server=1), (200, moved))
        self.login('ada', server=1)
        self.assertEqual(self.request('POST', '/_test/reset', fixture(), server=1)[0], 204)
        self.error(self.request('GET', '/reservations', token=self.ada, server=1), 401, 'unauthenticated')

    def test_invalid_import_is_all_or_nothing(self):
        self.create()
        baseline = self.snapshot()
        broken = [{}, {**baseline, 'track': 'wrong'}, {**baseline, 'format_version': True}, {**baseline, 'state': []}]
        for key, value in [('users', []), ('sessions', {'invalid': 'ada'}), ('restaurants', []), ('reservations', [{}]), ('receipts', [{}])]:
            bad = copy.deepcopy(baseline)
            bad['state'][key] = value
            broken.append(bad)
        for bad in broken:
            self.error(self.request('POST', '/_test/import', bad), 422, 'validation_failed')
            self.assertTrue(baseline == self.snapshot(), 'rejected import changed destination')

    def test_reset_seeds_and_clears_receipts(self):
        seed = fixture()
        seed['reservations'] = [{**self.booking(), 'id': 'seed-id', 'reference': 'SEED01', 'user_id': 'ada'}]
        self.assertEqual(self.request('POST', '/_test/reset', seed)[0], 204)
        self.error(self.request('GET', '/reservations', token=self.ada), 401, 'unauthenticated')
        self.ada = self.login('ada')
        record = self.request('GET', '/reservations/SEED01', token=self.ada)[1]
        self.assertEqual(record['reservation_id'], 'seed-id')
        self.error(self.request('POST', '/reservations', self.booking(), self.ada, 'new'), 409, 'table_unavailable')
        self.request('POST', '/reservations/SEED01/cancel', {}, self.ada)
        self.create('new')

    def test_fixture_numeric_type_codes_without_mutation(self):
        baseline = self.snapshot()
        for name in ['slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'capacity']:
            for value in ['30', True, [], {}, None, -1, 0.5]:
                seed = fixture()
                target = seed['restaurants'][0]
                if name == 'capacity':
                    target = target['tables'][0]
                target[name] = value
                wrong_type = type(value) not in (int, float)
                self.error(self.request('POST', '/_test/reset', seed), 400 if wrong_type else 422,
                           'malformed_request' if wrong_type else 'validation_failed')
                self.assertTrue(baseline == self.snapshot(), 'rejected fixture changed state')

    def test_table_ids_scoped_by_restaurant_and_import(self):
        seed = fixture()
        other = copy.deepcopy(seed['restaurants'][0])
        other['id'] = 'other'
        seed['restaurants'].append(other)
        seed['reservations'] = [{**self.booking(), 'id': 'seed-id', 'reference': 'SEED01', 'user_id': 'ada'}]
        self.assertEqual(self.request('POST', '/_test/reset', seed)[0], 204)
        self.ada = self.login('ada')
        available = self.request('GET', '/availability?restaurant_id=other&date=2032-10-25&party_size=2')[1]
        self.assertIn('t1', next(s for s in available['slots'] if s['starts_at_local'].endswith('19:00'))['available_table_ids'])
        other_record = self.create('other', restaurant_id='other')
        self.error(self.request('POST', '/reservations', self.booking(restaurant_id='other'), self.ada, 'conflict'), 409, 'table_unavailable')
        self.error(self.request('POST', '/reservations', self.booking(), self.ada, 'conflict'), 409, 'table_unavailable')
        self.error(self.request('POST', '/reservation-moves', {'moves': [{'reference': 'SEED01'}, {'reference': other_record['reference']}]}, self.ada, 'mixed'), 422, 'validation_failed')
        snapshot = self.snapshot()
        self.assertEqual(self.request('POST', '/_test/import', snapshot, server=1)[0], 204)
        self.assertTrue(snapshot == self.snapshot(server=1), 'cross-restaurant import changed state')
        self.assertEqual(self.request('POST', '/reservations', self.booking(restaurant_id='other'), self.ada, 'other', server=1), (200, other_record))
        duplicate = copy.deepcopy(seed)
        duplicate['restaurants'][0]['tables'].append(duplicate['restaurants'][0]['tables'][0])
        self.error(self.request('POST', '/_test/reset', duplicate), 422, 'validation_failed')

    def test_deep_bodies_create_moves_replay_and_portable_snapshots(self):
        # Use raw JSON so the client's own call stack is not the tested limit.
        for depth in [600, 1200]:
            self.request('POST', '/_test/reset', fixture())
            self.ada = self.login('ada')
            nested = '{"a":[' * depth + '1' + ']}' * depth
            def encoded(body, value=nested):
                return (json.dumps(body)[:-1] + ',"ignored":' + value + '}').encode()
            for malformed in ['[1,]', '{"x":1,}', '{"x":}', '01', 'true false', 'NaN', 'Infinity']:
                invalid = encoded(self.booking(), '{"a":[' * depth + malformed + ']}' * depth)
                self.error(self.request('POST', '/reservations', token=self.ada, key='deep', raw=invalid), 400, 'malformed_request')
            raw = encoded(self.booking())
            created = self.request('POST', '/reservations', token=self.ada, key='deep', raw=raw)
            self.assertEqual(created[0], 201)
            self.assertEqual(self.request('POST', '/reservations', token=self.ada, key='deep', raw=raw), (200, created[1]))
            different = encoded(self.booking(), '{"a":[' * depth + 'true' + ']}' * depth)
            self.error(self.request('POST', '/reservations', token=self.ada, key='deep', raw=different), 409, 'idempotency_key_reuse')
            move = {'moves': [{'reference': created[1]['reference'], 'table_id': 't2'}]}
            moved = self.request('POST', '/reservation-moves', token=self.ada, key='deep', raw=encoded(move))
            self.assertEqual(moved[0], 201)
            with urlopen(self.urls[0] + '/_test/export', timeout=10) as response:
                self.assertEqual(response.status, 200)
                exported = response.read()
            # Keep exported credentials only in memory; do not put them in assertions.
            self.assertEqual(self.request('POST', '/_test/import', server=1, raw=exported)[0], 204)
            self.assertEqual(self.request('POST', '/reservations', token=self.ada, key='deep', raw=raw, server=1), (200, created[1]))
            self.assertEqual(self.request('POST', '/reservation-moves', token=self.ada, key='deep', raw=encoded(move), server=1), (200, moved[1]))
            bad = {'moves': [{'reference': created[1]['reference'], 'party_size': False}]}
            self.error(self.request('POST', '/reservation-moves', token=self.ada, key='failed', raw=encoded(bad)), 422, 'validation_failed')
            current = self.request('GET', '/reservations/' + created[1]['reference'], token=self.ada)[1]
            self.assertEqual(current['table_id'], 't2')
            self.assertEqual(self.request('POST', '/reservation-moves', token=self.ada, key='failed', raw=encoded(move))[0], 201)

    def test_opaque_restaurant_id_routes_decode_one_segment_once(self):
        seed = fixture()
        ids = ['branch/one', 'filial/ação', 'branch%2Fone', 'x?y#z', '../reservations', 'with space']
        seed['restaurants'] = [{**copy.deepcopy(seed['restaurants'][0]), 'id': rid} for rid in ids]
        self.assertEqual(self.request('POST', '/_test/reset', seed)[0], 204)
        self.assertEqual([r['id'] for r in self.request('GET', '/restaurants')[1]['restaurants']], ids)
        for rid in ids:
            self.assertEqual(self.request('GET', '/restaurants/' + quote(rid, safe=''))[1]['id'], rid)
            query = urlencode({'restaurant_id': rid, 'date': '2032-10-25', 'party_size': 2})
            self.assertEqual(self.request('GET', '/availability?' + query)[0], 200)
        for rid in ['unknown/name', 'missing%2Fname', 'missing/ação']:
            self.error(self.request('GET', '/restaurants/' + quote(rid, safe='')), 404, 'not_found')
        self.error(self.request('GET', '/reservations/anything%2Felse'), 401, 'unauthenticated')
        self.error(self.request('POST', '/reservations/anything/cancel', {}), 401, 'unauthenticated')
        self.ada = self.login('ada')
        record = self.create('opaque', restaurant_id='branch/one')
        encoded_reference = ''.join('%' + format(ord(c), '02X') for c in record['reference'])
        self.assertEqual(self.request('GET', '/reservations/' + encoded_reference, token=self.ada), (200, record))


class TransactionFailure(unittest.TestCase):
    def test_mutation_rolls_back_on_dispatch_and_encoding_failure(self):
        from engine import Engine
        engine = Engine()
        original = engine.state
        def failed_dispatch(*_args):
            engine.state['reservations'].append({'marker': 'must not commit'})
            raise ValueError('Injected failure after mutation')
        engine.dispatch = failed_dispatch
        with self.assertRaises(ValueError):
            engine.handle('POST', '/reservations', {}, {}, {})
        self.assertIs(engine.state, original)
        self.assertEqual(engine.state['reservations'], [])
        def failed_encoding(*_args):
            engine.state['receipts'].append({'marker': 'must not commit'})
            return 201, {'invalid': object()}
        engine.dispatch = failed_encoding
        with self.assertRaises(TypeError):
            engine.handle('POST', '/reservation-moves', {}, {}, {})
        self.assertIs(engine.state, original)
        self.assertEqual(engine.state['receipts'], [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
