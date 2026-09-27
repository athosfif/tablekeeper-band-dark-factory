"""JSON-only state, constructed and validated before atomic replacement."""
from copy import deepcopy
import json
import re
from datetime import datetime
from urllib.parse import unquote

from domain import available, proposal, reference, restaurant_config
from security import hash_password, valid_hash
from timekeeping import instant, now
from policies import base_terms, bounded_integer, policy_body, terms_of
from ledger import append_event
from validation import APIError, email, field, identifier, object_body, require, same_json

LEGACY_KEYS = {'users', 'restaurants', 'reservations', 'tokens', 'receipts'}
STATE_KEYS = LEGACY_KEYS | {'policies', 'histories', 'series', 'restaurant_revisions'}
RECORD_KEYS = {'reservation_id', 'reference', 'restaurant_id', 'party_size',
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
        state['policies'][restaurant['id']] = []
        state['restaurant_revisions'][restaurant['id']] = 0
    ids = set()
    for body in field(body, 'reservations', list):
        object_body(body)
        candidate = proposal(state['restaurants'], body)
        uid = identifier(body, 'user_id')
        rid = identifier(body, 'id')
        ref = reference(field(body, 'reference', str))
        require(uid in state['users'] and rid not in ids and ref not in state['reservations'])
        status = field(body, 'status', str) if 'status' in body else 'confirmed'
        require(status in ('confirmed', 'cancelled'))
        if status == 'confirmed':
            require(available(candidate, state['reservations']), 'table_unavailable', 409)
        state['reservations'][ref] = {**candidate, 'reservation_id': rid, 'reference': ref,
                                      'user_id': uid, 'status': status, 'created_at': now().isoformat(), 'revision': 1}
        state['histories'][ref] = []
        if status == 'confirmed':
            append_event(state, state['reservations'][ref], 'created')
        ids.add(rid)
    return state


def validate_terms(terms, restaurant, state):
    require(type(terms) is dict)
    version = bounded_integer(terms.get('policy_version'), 0)
    choices = state['policies'][restaurant['id']]
    require(version <= len(choices))
    expected = base_terms(restaurant) if version == 0 else terms_of(choices[version - 1])
    require(same_json(terms, expected))


def validate_record(record, state, *, owner=None, legacy=False):
    require(type(record) is dict)
    modern = 'revision' in record or 'accepted_terms' in record
    require(modern or legacy)
    keys = RECORD_KEYS | ({'revision', 'accepted_terms'} if modern else set())
    require(set(record) in (keys | {'table_id'}, keys | {'table_ids'}, keys | {'table_id', 'table_ids'}))
    identifier(record, 'reservation_id')
    reference(record['reference'])
    require(record['user_id'] in state['users'])
    if owner is not None:
        require(record['user_id'] == owner)
    require(record['status'] in ('confirmed', 'cancelled'))
    restaurant = state['restaurants'][record['restaurant_id']]
    terms = record['accepted_terms'] if modern else base_terms(restaurant)
    validate_terms(terms, restaurant, state)
    revision = bounded_integer(record['revision']) if modern else 1
    body = {k: v for k, v in record.items() if k != 'table_id' or 'table_ids' not in record}
    expected = proposal(state['restaurants'], body, terms=terms)
    # Old stage-1 receipts legitimately have no table_ids. Validate without
    # decorating those immutable responses; only live records are migrated.
    require(all(same_json(record[k], v) for k, v in expected.items()
                if (k != 'table_ids' or 'table_ids' in record) and (k != 'accepted_terms' or modern)))
    if 'table_ids' in record:
        require(('table_id' in record) == (len(record['table_ids']) == 1))
    created = datetime.fromisoformat(field(record, 'created_at', str))
    require(created.tzinfo is not None)
    return {**record, **expected, 'revision': revision}


def validate_history(entries, record, state):
    require(type(entries) is list)
    prior_at, prior_revision = None, 0
    for seq, entry in enumerate(entries, 1):
        require(type(entry) is dict and set(entry) == {'seq', 'at', 'event', 'changes', 'revision', 'accepted_terms'})
        require(type(entry['seq']) is int and entry['seq'] == seq)
        at = datetime.fromisoformat(field(entry, 'at', str))
        require(at.tzinfo is not None and (prior_at is None or at >= prior_at))
        revision = bounded_integer(entry['revision'])
        require(prior_revision < revision <= record['revision'])
        validate_terms(entry['accepted_terms'], state['restaurants'][record['restaurant_id']], state)
        event = entry['event']
        require(event in ('created', 'changed', 'cancelled'))
        delta = field(entry, 'changes', list)
        if event == 'cancelled':
            require(not delta and seq == len(entries) and record['status'] == 'cancelled')
        else:
            require(bool(delta))
            names = []
            for change in delta:
                require(type(change) is dict and set(change) == {'field', 'from', 'to'})
                require(change['field'] in ('table_id', 'table_ids', 'starts_at_local', 'party_size'))
                require(not same_json(change['from'], change['to']))
                names.append(change['field'])
            order = {'table_id': 0, 'table_ids': 0, 'starts_at_local': 1, 'party_size': 2}
            require([order[n] for n in names] == sorted(set(order[n] for n in names)))
            if event == 'created':
                require(seq == 1 and revision == 1 and len(delta) == 3 and all(c['from'] is None for c in delta))
        prior_at, prior_revision = at, revision
    if entries:
        require(entries[-1]['revision'] == record['revision'] and same_json(entries[-1]['accepted_terms'], record['accepted_terms']))
    else:
        require(record['revision'] == 1)


def validate_series(series, state):
    require(type(series) is dict and set(series) == {'series_id', 'user_id', 'restaurant_id', 'revision', 'interval_weeks', 'occurrences'})
    identifier(series, 'series_id')
    require(series['user_id'] in state['users'] and series['restaurant_id'] in state['restaurants'])
    bounded_integer(series['revision'])
    bounded_integer(series['interval_weeks'], 1, 4)
    occurrences = field(series, 'occurrences', list)
    require(2 <= len(occurrences) <= 12)
    refs = []
    for i, occurrence in enumerate(occurrences):
        require(type(occurrence) is dict and set(occurrence) == {'index', 'reference', 'exception'})
        require(type(occurrence['index']) is int and occurrence['index'] == i and type(occurrence['exception']) is bool)
        record = state['reservations'][reference(occurrence['reference'])]
        require(record['user_id'] == series['user_id'] and record['restaurant_id'] == series['restaurant_id'])
        refs.append(occurrence['reference'])
    require(len(refs) == len(set(refs)))
    return refs


def imported_state(envelope):
    """An invalid snapshot never escapes into the live store, including malformed internals."""
    try:
        require(envelope.get('track') == 'tablekeeper')
        require(type(envelope.get('format_version')) is int and envelope['format_version'] == 1)
        candidate = envelope.get('state')
        require(type(candidate) is dict and set(candidate) in (STATE_KEYS, LEGACY_KEYS))
        require(all(type(v) is dict for v in candidate.values()))
        legacy = set(candidate) == LEGACY_KEYS
        state = deepcopy(candidate)
        if legacy:
            state.update(policies={rid: [] for rid in state['restaurants']},
                         histories={ref: [] for ref in state['reservations']}, series={},
                         restaurant_revisions={rid: 0 for rid in state['restaurants']})
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
            comparable = {k: v for k, v in validated.items() if k in restaurant}
            require(validated['id'] == rid and same_json(comparable, restaurant))
            state['restaurants'][rid] = validated
        require(set(state['policies']) == set(state['restaurants']) == set(state['restaurant_revisions']))
        for rid, policies in state['policies'].items():
            require(type(policies) is list)
            bounded_integer(state['restaurant_revisions'][rid], 0)
            for index, policy in enumerate(policies, 1):
                require(type(policy) is dict)
                expected = {**policy_body(policy, state['restaurants'][rid]), 'policy_version': index}
                require(same_json(policy, expected))
        for token, uid in state['tokens'].items():
            require(type(token) is str and bool(token) and type(uid) is str and uid in state['users'])
        checked = {}
        ids = set()
        for ref, reservation in state['reservations'].items():
            reservation = validate_record(reservation, state, legacy=legacy)
            state['reservations'][ref] = reservation
            require(ref == reservation['reference'] and reservation['reservation_id'] not in ids)
            ids.add(reservation['reservation_id'])
            if reservation['status'] == 'confirmed':
                require(available(reservation, checked))
            checked[ref] = reservation
        require(set(state['histories']) == set(state['reservations']))
        for ref, entries in state['histories'].items():
            validate_history(entries, state['reservations'][ref], state)
        adopted = set()
        for sid, series in state['series'].items():
            refs = validate_series(series, state)
            require(sid == series['series_id'] and not adopted.intersection(refs))
            adopted.update(refs)
        for namespace, receipt in state['receipts'].items():
            parts = json.loads(namespace)
            require(type(parts) is list and len(parts) == 4 and all(type(p) is str for p in parts))
            uid, method, path, key = parts
            require(namespace == receipt_key(uid, path, key))
            policy_route = re.fullmatch(r'/restaurants/([^/]+)/policies', path)
            require(uid in state['users'] and method == 'POST' and 1 <= len(key) <= 255
                    and (path in ('/reservations', '/reservation-moves', '/series') or policy_route))
            require(type(receipt) is dict and set(receipt) == {'body', 'response'})
            object_body(receipt['body'])
            response = receipt['response']
            if policy_route:
                rid = unquote(policy_route[1])
                require(uid in state['restaurants'][rid]['manager_user_ids'])
                require(any(same_json(response, policy) for policy in state['policies'][rid]))
                continue
            if path == '/series':
                require(type(response) is dict and set(response) == {'series_id', 'revision', 'interval_weeks', 'occurrences'})
                current = state['series'][response['series_id']]
                require(current['user_id'] == uid and response['revision'] == 1
                        and response['interval_weeks'] == current['interval_weeks'])
                require(type(response['occurrences']) is list and len(response['occurrences']) == len(current['occurrences']))
                records = []
                for occurrence, existing in zip(response['occurrences'], current['occurrences']):
                    require(type(occurrence) is dict and set(occurrence) == {'index', 'reference', 'exception', 'reservation'})
                    require(occurrence['index'] == existing['index'] and occurrence['reference'] == existing['reference']
                            and occurrence['exception'] is False and occurrence['reservation']['reference'] == occurrence['reference'])
                    records.append(occurrence['reservation'])
            elif path == '/reservation-moves':
                require(type(response) is dict and set(response) == {'reservations'})
                records = field(response, 'reservations', list)
                require(1 <= len(records) <= 8)
            else:
                records = [response]
            for record in records:
                validate_record({**record, 'user_id': uid}, state, owner=uid, legacy=True)
                current = state['reservations'][record['reference']]
                require(current['reservation_id'] == record['reservation_id']
                        and current['created_at'] == record['created_at'] and current['user_id'] == uid)
        return state
    except (APIError, ValueError, TypeError, KeyError, OverflowError, RecursionError):
        from validation import fail
        fail('validation_failed', 422, 'Invalid portable state')


def receipt_key(uid, path, key):
    return json.dumps([uid, 'POST', path, key], ensure_ascii=True, separators=(',', ':'))
