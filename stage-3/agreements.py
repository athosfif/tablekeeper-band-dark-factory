"""Calendar recurrence: prepare all occurrences, then adopt in one transaction."""
from datetime import timedelta
import secrets

from domain import available, check_cutoff, members, proposal
from ledger import append_event, bump_restaurant, new_record, public_series
from policies import bounded_integer
from timekeeping import local_time
from validation import field, require, fail


def adopt(state, uid, body):
    ref = field(body, 'anchor_reference', str)
    count = bounded_integer(body.get('count'), 2, 12)
    weeks = bounded_integer(body.get('interval_weeks'), 1, 4)
    anchor = state['reservations'].get(ref)
    require(anchor is not None and anchor['user_id'] == uid, 'not_found', 404)
    require(anchor['status'] == 'confirmed', 'reservation_cancelled', 409)
    require(not any(o['reference'] == ref for s in state['series'].values() for o in s['occurrences']),
            'already_in_series', 409)
    check_cutoff(anchor)
    local = local_time(anchor['starts_at_local'])
    prepared = {}
    for index in range(1, count):
        try:
            next_local = (local + timedelta(days=index * weeks * 7)).isoformat(timespec='minutes')
        except OverflowError:
            fail()
        candidate = proposal(state['restaurants'], {'restaurant_id': anchor['restaurant_id'],
                            'table_ids': members(anchor), 'party_size': anchor['party_size'],
                            'starts_at_local': next_local}, state['policies'])
        # Index order includes occupancy: a later field error cannot mask this conflict.
        require(available(candidate, state['reservations']) and available(candidate, prepared), 'table_unavailable', 409)
        record = new_record(candidate, uid, state['reservations'] | prepared)
        prepared[record['reference']] = record
    sid = 'series_' + secrets.token_hex(16)
    while sid in state['series']:
        sid = 'series_' + secrets.token_hex(16)
    series = {'series_id': sid, 'user_id': uid, 'restaurant_id': anchor['restaurant_id'],
              'revision': 1, 'interval_weeks': weeks,
              'occurrences': [{'index': i, 'reference': value, 'exception': False}
                              for i, value in enumerate([ref, *prepared])]}
    state['reservations'].update(prepared)
    for record in prepared.values():
        append_event(state, record, 'created')
    state['series'][sid] = series
    bump_restaurant(state, anchor['restaurant_id'])
    return public_series(series, state)
