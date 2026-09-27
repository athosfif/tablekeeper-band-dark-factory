"""Reservation events and related counters, committed only after validation."""
from copy import deepcopy
import secrets

from domain import members, public_record
from timekeeping import instant, now


def new_record(candidate, uid, existing):
    ref = secrets.token_hex(5).upper()
    while ref in existing:
        ref = secrets.token_hex(5).upper()
    return {**candidate, 'reservation_id': 'res_' + secrets.token_hex(16), 'reference': ref,
            'user_id': uid, 'status': 'confirmed', 'created_at': now().isoformat(), 'revision': 1}


def changes(before, after):
    result = []
    old_ids, new_ids = members(before) if before else None, members(after)
    if old_ids != new_ids:
        pair = len(new_ids) == 2 or old_ids is not None and len(old_ids) == 2
        result.append({'field': 'table_ids' if pair else 'table_id',
                       'from': (old_ids if pair else old_ids[0]) if before else None,
                       'to': new_ids if pair else new_ids[0]})
    for key in ('starts_at_local', 'party_size'):
        if before is None or before[key] != after[key]:
            result.append({'field': key, 'from': before[key] if before else None, 'to': after[key]})
    return result


def append_event(state, record, event, before=None):
    entries = state['histories'].setdefault(record['reference'], [])
    at = record['created_at'] if event == 'created' else now().isoformat()
    if entries and instant(at) < instant(entries[-1]['at']):
        at = entries[-1]['at']
    entries.append(deepcopy({'seq': len(entries) + 1, 'at': at, 'event': event,
                            'changes': [] if event == 'cancelled' else changes(before, record),
                            'revision': record['revision'], 'accepted_terms': record['accepted_terms']}))


def bump_restaurant(state, rid):
    state['restaurant_revisions'][rid] += 1


def commit_changes(state, candidates, event='changed'):
    changed_refs, restaurants = set(), set()
    for record in candidates:
        before = state['reservations'][record['reference']]
        if record['revision'] == before['revision']:
            continue
        state['reservations'][record['reference']] = record
        append_event(state, record, event, before)
        changed_refs.add(record['reference'])
        restaurants.add(record['restaurant_id'])
    for series in state['series'].values():
        affected = [o for o in series['occurrences'] if o['reference'] in changed_refs]
        if affected:
            series['revision'] += 1
            if event == 'changed':
                for occurrence in affected:
                    occurrence['exception'] = True
    for rid in restaurants:
        bump_restaurant(state, rid)


def public_series(series, state):
    return {k: deepcopy(series[k]) for k in ('series_id', 'revision', 'interval_weeks')} | {
        'occurrences': [{**o, 'reservation': public_record(state['reservations'][o['reference']])}
                        for o in series['occurrences']]}
