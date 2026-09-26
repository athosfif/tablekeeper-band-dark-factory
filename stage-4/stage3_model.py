"""Dated policies, immutable booking terms/history, and portable state validation."""

from urllib.parse import unquote
import stage2_model as previous
from stage2_model import *

POLICY_FIELDS = ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes',
                 'opening_hours', 'capacities')


def policy_zero(r):
    return {'policy_version': 0, **{k: clone(r[k]) for k in POLICY_FIELDS if k != 'capacities'},
            'capacities': {t['id']: t['capacity'] for t in r['tables']}}


def policy_body(r, body):
    """Policy-specific invalid type and shape rules always yield 422."""
    try:
        obj(body)
        effective = field(body, 'effective_from')
        local_date(effective)
        result = {'effective_from': effective}
        for key, low, high in [('slot_minutes', 1, 1440), ('reservation_duration_minutes', 1, 1440),
                               ('cancellation_cutoff_minutes', 0, 10080)]:
            value = integer(body[key], low)
            require(value <= high)
            result[key] = value
        hours = field(body, 'opening_hours', list)
        seen, normalized = set(), []
        for h in hours:
            obj(h)
            day = field(h, 'weekday')
            require(day in DAYS and day not in seen)
            seen.add(day)
            opens, closes = field(h, 'opens'), field(h, 'closes')
            require(clock_minutes(opens) < clock_minutes(closes))
            normalized.append({'weekday': day, 'opens': opens, 'closes': closes})
        result['opening_hours'] = normalized
        capacities = field(body, 'capacities', dict)
        require(set(capacities) == {t['id'] for t in r['tables']})
        result['capacities'] = {tid: integer(value) for tid, value in capacities.items()}
        require(all(value <= 100 for value in result['capacities'].values()))
        return result
    except (APIError, KeyError, TypeError, ValueError, OverflowError):
        raise APIError(message='Invalid complete policy') from None


def selected_policy(state, r, day):
    eligible = [p for p in state['policies'][r['id']] if p['effective_from'] <= day]
    if not eligible:
        return policy_zero(r)
    policy = max(eligible, key=lambda p: (p['effective_from'], p['policy_version']))
    return {k: clone(v) for k, v in policy.items() if k != 'effective_from'}


def rules_restaurant(r, terms):
    return {**r, **{k: terms[k] for k in POLICY_FIELDS if k != 'capacities'},
            'tables': [{**t, 'capacity': terms['capacities'][t['id']]} for t in r['tables']]}


def booking_fields(state, body, terms=None):
    rid = identifier(field(body, 'restaurant_id'))
    wall = local_datetime(field(body, 'starts_at_local'))
    r = restaurant(state, rid)
    terms = terms if terms is not None else selected_policy(state, r, wall.date().isoformat())
    fields = previous.booking_fields({'restaurants': [rules_restaurant(r, terms)]}, body)
    return {**fields, 'accepted_terms': clone(terms)}


def check_cutoff(state, reservation):
    remaining = (instant(reservation['starts_at']) - datetime.now(UTC)).total_seconds() / 60
    require(remaining > reservation['accepted_terms']['cancellation_cutoff_minutes'], 409, 'cutoff_passed')


def changes_between(old, new):
    before = selected_tables(old) if old else None
    after = selected_tables(new)
    changes = []
    if before != after:
        pair = len(after) > 1 or (before is not None and len(before) > 1)
        changes.append({'field': 'table_ids' if pair else 'table_id',
                        'from': before if pair else before[0] if before else None,
                        'to': list(after) if pair else after[0]})
    for key in ('starts_at_local', 'party_size'):
        value = old[key] if old else None
        if value != new[key]:
            changes.append({'field': key, 'from': value, 'to': new[key]})
    return changes


def history_event(state, record, event, changes, at=None, **extra):
    entries = state['histories'].setdefault(record['reference'], [])
    now = at or datetime.now(UTC).isoformat()
    if entries and instant(now) < instant(entries[-1]['at']):
        now = entries[-1]['at']
    entries.append({'seq': len(entries) + 1, 'at': now, 'event': event,
                    'changes': clone(changes), 'revision': record['revision'],
                    'accepted_terms': clone(record['accepted_terms']), **extra})


def empty_state():
    return {**previous.empty_state(), 'schema_stage': 3, 'policies': {}, 'histories': {},
            'restaurant_revisions': {}, 'series': []}


def upgrade(state):
    state.update(schema_stage=3, policies={r['id']: [] for r in state['restaurants']},
                 histories={}, restaurant_revisions={r['id']: 0 for r in state['restaurants']}, series=[])
    for record in state['reservations']:
        record.update(revision=1, accepted_terms=policy_zero(restaurant(state, record['restaurant_id'])))
        history_event(state, record, 'created', changes_between(None, record), record['created_at'])
    return state


def fixture_state(body):
    state = upgrade(previous.fixture_state(body))
    users = {u['id'] for u in state['users']}
    for source, r in zip(body['restaurants'], state['restaurants']):
        if 'manager_user_ids' in source:
            managers = field(source, 'manager_user_ids', list)
            require(all(identifier(uid) in users for uid in managers))
            require(len(set(managers)) == len(managers))
            r['manager_user_ids'] = list(managers)
    return state


def imported_state(envelope):
    """Validate the whole detached graph, preserving immutable original receipts."""
    try:
        if isinstance(envelope.get('state'), dict) and envelope['state'].get('schema_stage', 1) in (1, 2):
            return upgrade(previous.imported_state(envelope))
        require(envelope['track'] == 'tablekeeper' and type(envelope['format_version']) is int
                and envelope['format_version'] == 1)
        state = clone(envelope['state'])
        require(isinstance(state, dict) and set(state) == set(empty_state()))
        require(type(state['schema_stage']) is int and state['schema_stage'] == 3)
        # Reuse the accepted validator for immutable catalogue, password and session data.
        core = {k: clone(state[k]) for k in previous.empty_state()}
        core.update(schema_stage=2, reservations=[], receipts=[])
        for r in core['restaurants']:
            r.pop('manager_user_ids', None)
        previous.imported_state({'track': 'tablekeeper', 'format_version': 1, 'state': core})
        users = {u['id'] for u in state['users']}
        restaurants = {r['id']: r for r in state['restaurants']}
        require(isinstance(state['policies'], dict) and set(state['policies']) == set(restaurants))
        require(isinstance(state['restaurant_revisions'], dict) and set(state['restaurant_revisions']) == set(restaurants))
        for rid, r in restaurants.items():
            managers = r.get('manager_user_ids', [])
            require(isinstance(managers, list) and all(isinstance(u, str) and u in users for u in managers)
                    and len(set(managers)) == len(managers))
            revision = state['restaurant_revisions'][rid]
            require(type(revision) is int and revision >= 0)
            policies = state['policies'][rid]
            require(isinstance(policies, list))
            for n, policy in enumerate(policies, 1):
                require(json_equal(policy, {**policy_body(r, policy), 'policy_version': n}))

        def valid_terms(rid, terms):
            require(isinstance(terms, dict))
            version = terms['policy_version']
            require(type(version) is int and 0 <= version <= len(state['policies'][rid]))
            wanted = policy_zero(restaurants[rid]) if version == 0 else {
                k: v for k, v in state['policies'][rid][version - 1].items() if k != 'effective_from'}
            require(json_equal(terms, wanted))

        def valid_record(record, owner=False):
            require(isinstance(record, dict))
            old = 'revision' not in record and 'accepted_terms' not in record
            ids = selected_tables(record)
            keys = {'reservation_id', 'reference', 'restaurant_id', 'party_size', 'status',
                    'starts_at_local', 'starts_at', 'ends_at', 'created_at'}
            if 'table_ids' in record:
                keys.add('table_ids')
            if len(ids) == 1:
                keys.add('table_id')
            if not old:
                keys.update(('revision', 'accepted_terms'))
                require(type(record['revision']) is int and record['revision'] >= 1)
            if owner:
                keys.add('user_id')
                require(record['user_id'] in users and not old and 'table_ids' in record)
            require(set(record) == keys and isinstance(ids, list))
            identifier(record['reservation_id'])
            require(re.fullmatch(r'[A-Z0-9]{6,12}', record['reference']) is not None)
            require(record['status'] in ('confirmed', 'cancelled'))
            instant(record['created_at'])
            rid = record['restaurant_id']
            terms = policy_zero(restaurants[rid]) if old else record['accepted_terms']
            valid_terms(rid, terms)
            request = {k: record[k] for k in ('restaurant_id', 'party_size', 'starts_at_local')}
            request['table_ids'] = ids
            fields = booking_fields(state, request, terms)
            for key, value in fields.items():
                if key == 'accepted_terms' and old or key == 'table_ids' and key not in record:
                    continue
                require(json_equal(record[key], value))
            return terms

        require(isinstance(state['reservations'], list) and isinstance(state['histories'], dict))
        refs, ids = {}, set()
        for record in state['reservations']:
            valid_record(record, True)
            require(record['reference'] not in refs and record['reservation_id'] not in ids)
            refs[record['reference']] = record
            ids.add(record['reservation_id'])
        require(set(state['histories']) == set(refs))
        for ref, record in refs.items():
            entries = state['histories'][ref]
            require(isinstance(entries, list) and entries)
            prior, last_at, cancelled = None, None, False
            for n, entry in enumerate(entries, 1):
                require(set(entry) == {'seq', 'at', 'event', 'changes', 'revision', 'accepted_terms'})
                require(type(entry['seq']) is int and entry['seq'] == n and not cancelled)
                at = instant(entry['at'])
                require(last_at is None or at >= last_at)
                last_at = at
                valid_terms(record['restaurant_id'], entry['accepted_terms'])
                require(type(entry['revision']) is int and entry['revision'] == n)
                if n == 1:
                    require(entry['event'] == 'created' and entry['at'] == record['created_at'])
                    fields = {c['field']: c['to'] for c in entry['changes']}
                    table_key = 'table_ids' if 'table_ids' in fields else 'table_id'
                    require([c['field'] for c in entry['changes']] == [table_key, 'starts_at_local', 'party_size'])
                    require(all(c['from'] is None and set(c) == {'field','from','to'} for c in entry['changes']))
                    fields['restaurant_id'] = record['restaurant_id']
                else:
                    require(entry['event'] in ('changed', 'cancelled'))
                    fields = {k: prior[k] for k in ('restaurant_id', 'starts_at_local', 'party_size')}
                    fields['table_ids'] = selected_tables(prior)
                    for change in entry['changes']:
                        require(set(change) == {'field', 'from', 'to'})
                        key = change['field']
                        require(key in ('table_id', 'table_ids', 'starts_at_local', 'party_size'))
                        before = selected_tables(prior) if key == 'table_ids' else prior.get(key)
                        require(json_equal(change['from'], before))
                        if key == 'table_id':
                            fields.pop('table_ids', None)
                        fields[key] = change['to']
                resulting = booking_fields(state, fields, entry['accepted_terms'])
                if entry['event'] == 'cancelled':
                    require(entry['changes'] == [] and json_equal(prior['accepted_terms'], entry['accepted_terms']))
                    cancelled = True
                elif n > 1:
                    require(entry['changes'] and json_equal(entry['changes'], changes_between(prior, resulting)))
                prior = resulting
            require(record['revision'] == len(entries))
            require(all(json_equal(record[k], v) for k, v in prior.items()))
            require(not cancelled or record['status'] == 'cancelled')
        records = list(refs.values())
        for n, record in enumerate(records):
            require(not any(overlap(record, other) for other in records[n + 1:]))

        require(isinstance(state['series'], list))
        series_ids, adopted = set(), set()
        for series in state['series']:
            require(set(series) == {'series_id', 'user_id', 'restaurant_id', 'revision', 'interval_weeks', 'occurrences'})
            sid = identifier(series['series_id'])
            require(sid not in series_ids and series['user_id'] in users and series['restaurant_id'] in restaurants)
            series_ids.add(sid)
            require(type(series['revision']) is int and series['revision'] >= 1)
            require(type(series['interval_weeks']) is int and 1 <= series['interval_weeks'] <= 4)
            occurrences = series['occurrences']
            require(isinstance(occurrences, list) and 2 <= len(occurrences) <= 12)
            first_date = None
            for n, occurrence in enumerate(occurrences):
                require(set(occurrence) == {'index', 'reference', 'exception', 'scheduled_date'})
                require(type(occurrence['index']) is int and occurrence['index'] == n and type(occurrence['exception']) is bool)
                ref = occurrence['reference']
                require(ref in refs and ref not in adopted)
                adopted.add(ref)
                require(refs[ref]['user_id'] == series['user_id'] and refs[ref]['restaurant_id'] == series['restaurant_id'])
                day = local_date(occurrence['scheduled_date'])
                if first_date is None:
                    first_date = day
                require(day == first_date + timedelta(weeks=n * series['interval_weeks']))

        def receipt_record(record, uid):
            valid_record(record)
            current = refs[record['reference']]
            require(current['user_id'] == uid)
            for key in ('reservation_id', 'created_at', 'restaurant_id'):
                require(record[key] == current[key])
            if 'revision' in record:
                require(record['revision'] <= current['revision'])

        scopes = set()
        require(isinstance(state['receipts'], list))
        for receipt in state['receipts']:
            require(set(receipt) == {'user_id', 'method', 'path', 'key', 'body', 'response'})
            uid, path, body, response = (receipt[k] for k in ('user_id', 'path', 'body', 'response'))
            require(uid in users and receipt['method'] == 'POST' and isinstance(path, str))
            require(isinstance(receipt['key'], str) and 1 <= len(receipt['key']) <= 255)
            require(isinstance(body, dict) and isinstance(response, dict))
            scope = (uid, path, receipt['key'])
            require(scope not in scopes)
            scopes.add(scope)
            if path == '/reservations':
                receipt_record(response, uid)
                terms = response.get('accepted_terms', policy_zero(restaurants[response['restaurant_id']]))
                if 'table_ids' not in response:
                    fields = legacy_model.booking_fields(state, body)
                else:
                    fields = booking_fields(state, body, terms)
                require(all(json_equal(response[k], v) for k, v in fields.items()
                            if k != 'accepted_terms' or k in response))
                require(response['status'] == 'confirmed')
            elif path == '/reservation-moves':
                require(set(response) == {'reservations'})
                result = response['reservations']
                moves = body['moves']
                require(isinstance(result, list) and isinstance(moves, list) and 1 <= len(moves) <= 8 and len(result) == len(moves))
                require(len({m['reference'] for m in moves}) == len(moves))
                require(len({r['restaurant_id'] for r in result}) == 1)
                for move, record in zip(moves, result):
                    receipt_record(record, uid)
                    require(move['reference'] == record['reference'] and record['status'] == 'confirmed')
                    for key in ('starts_at_local', 'party_size'):
                        if key in move:
                            require(json_equal(move[key], record[key]))
                    if 'table_id' in move or 'table_ids' in move:
                        # Stage1 receipts ignore table_ids; stage2+ receipts accept it.
                        if 'table_ids' in record:
                            require(selection(restaurants[record['restaurant_id']], move) == selected_tables(record))
                        elif 'table_id' in move:
                            require(move['table_id'] == record['table_id'])
            elif path == '/series':
                require(set(response) == {'series_id', 'revision', 'interval_weeks', 'occurrences'})
                current = next(s for s in state['series'] if s['series_id'] == response['series_id'])
                require(current['user_id'] == uid and response['revision'] == 1)
                require(body['count'] == len(response['occurrences']) == len(current['occurrences']))
                require(body['interval_weeks'] == response['interval_weeks'] == current['interval_weeks'])
                require(body['anchor_reference'] == response['occurrences'][0]['reference'])
                for n, (item, current_item) in enumerate(zip(response['occurrences'], current['occurrences'])):
                    require(set(item) == {'index','reference','exception','reservation'})
                    require(type(item['index']) is int and item['index'] == n and item['exception'] is False)
                    require(item['reference'] == current_item['reference'] == item['reservation']['reference'])
                    receipt_record(item['reservation'], uid)
            else:
                match = re.fullmatch(r'/restaurants/([^/]+)/policies', path)
                require(match is not None)
                rid = unquote(match[1])
                require(uid in restaurants[rid].get('manager_user_ids', []))
                version = response['policy_version']
                require(type(version) is int and 1 <= version <= len(state['policies'][rid]))
                require(json_equal(response, state['policies'][rid][version - 1]))
                require(json_equal(response, {**policy_body(restaurants[rid], body), 'policy_version': version}))
        return state
    except (APIError, legacy_model.APIError, KeyError, TypeError, ValueError, OverflowError, AttributeError, StopIteration):
        raise APIError(message='Invalid state export') from None
