"""Calendar recurrence: prepare all occurrences, then adopt in one transaction."""
from datetime import timedelta
import secrets

from domain import available, changed, check_cutoff, members, overlaps, proposal
from ledger import append_event, bump_restaurant, new_record, public_series, commit_changes
from policies import bounded_integer
from timekeeping import local_time, clock_time
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
        require(available(candidate, state['reservations'], closures=state['closures'].values()) and available(candidate, prepared), 'table_unavailable', 409)
        record = new_record(candidate, uid, state['reservations'] | prepared)
        prepared[record['reference']] = record
    sid = 'series_' + secrets.token_hex(16)
    while sid in state['series']:
        sid = 'series_' + secrets.token_hex(16)
    series = {'series_id': sid, 'user_id': uid, 'restaurant_id': anchor['restaurant_id'],
              'revision': 1, 'interval_weeks': weeks,
              'scheduled_dates': [(local + timedelta(days=i * weeks * 7)).date().isoformat() for i in range(count)],
              'occurrences': [{'index': i, 'reference': value, 'exception': False}
                              for i, value in enumerate([ref, *prepared])]}
    state['reservations'].update(prepared)
    for record in prepared.values():
        append_event(state, record, 'created')
    state['series'][sid] = series
    bump_restaurant(state, anchor['restaurant_id'])
    return public_series(series, state)


def amend(state, uid, sid, body):
    series = state['series'].get(sid)
    require(series is not None and series['user_id'] == uid, 'not_found', 404)
    expected = bounded_integer(body.get('expected_revision'))
    first = bounded_integer(body.get('from_index'), 0, len(series['occurrences']) - 1)
    time = body.get('local_time')
    require(type(time) is str)
    clock_time(time)
    require(expected == series['revision'], 'stale_revision', 409)
    candidates = []
    for occurrence in series['occurrences'][first:]:
        current = state['reservations'][occurrence['reference']]
        if occurrence['exception'] or current['status'] == 'cancelled':
            continue
        local = series['scheduled_dates'][occurrence['index']] + 'T' + time
        # Series-level no-ops are valid even after cutoff or an adverse policy.
        if local == current['starts_at_local']:
            continue
        candidates.append(changed(current, {'starts_at_local': local}, state['restaurants'], state['policies']))
    refs = {r['reference'] for r in candidates}
    # All non-occupancy validation finishes, in index order, before conflicts.
    for i, candidate in enumerate(candidates):
        require(available(candidate, state['reservations'], refs, state['closures'].values())
                and all(not overlaps(candidate, other) for other in candidates[:i]), 'table_unavailable', 409)
    commit_changes(state, candidates, mark_exceptions=False)
    return public_series(series, state)
