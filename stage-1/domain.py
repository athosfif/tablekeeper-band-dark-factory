"""Reservation rules independent of transport and storage mutation."""
import re
from datetime import timedelta

from timekeeping import clock_time, instant, interval, now, zone, WEEKDAYS
from validation import field, identifier, integer, object_body, party, require


def restaurant_config(body):
    object_body(body)
    result = {key: field(body, key, str) for key in ('name', 'timezone')}
    result['id'] = identifier(body, 'id')
    zone(result['timezone'])
    for key in ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes'):
        result[key] = integer(body, key, 0 if key == 'cancellation_cutoff_minutes' else 1)
    result['opening_hours'] = []
    for entry in field(body, 'opening_hours', list):
        object_body(entry)
        day = field(entry, 'weekday', str)
        require(day in WEEKDAYS and day not in [h['weekday'] for h in result['opening_hours']])
        opens, closes = field(entry, 'opens', str), field(entry, 'closes', str)
        require(clock_time(opens) < clock_time(closes))
        result['opening_hours'].append({'weekday': day, 'opens': opens, 'closes': closes})
    result['tables'] = []
    for entry in field(body, 'tables', list):
        object_body(entry)
        table = {'id': identifier(entry, 'id'), 'label': field(entry, 'label', str),
                 'capacity': integer(entry, 'capacity')}
        require(table['id'] not in [t['id'] for t in result['tables']])
        result['tables'].append(table)
    return result


def proposal(restaurants, body):
    rid = identifier(body, 'restaurant_id')
    tid = identifier(body, 'table_id')
    size = party(body)
    local = field(body, 'starts_at_local', str)
    require(rid in restaurants, 'not_found', 404)
    restaurant = restaurants[rid]
    table = next((t for t in restaurant['tables'] if t['id'] == tid), None)
    require(table is not None, 'not_found', 404)
    require(size <= table['capacity'], 'party_exceeds_capacity')
    start, end = interval(restaurant, local)
    return {'restaurant_id': rid, 'table_id': tid, 'party_size': size,
            'starts_at_local': local, 'starts_at': start.isoformat(), 'ends_at': end.isoformat()}


def overlaps(a, b):
    return (a['restaurant_id'] == b['restaurant_id'] and a['table_id'] == b['table_id']
            and instant(a['starts_at']) < instant(b['ends_at'])
            and instant(b['starts_at']) < instant(a['ends_at']))


def available(candidate, reservations, exclude=()):
    return all(r['reference'] in exclude or r['status'] != 'confirmed' or not overlaps(candidate, r)
               for r in reservations.values())


def check_cutoff(reservation, restaurant):
    # Difference avoids overflow from unbounded but valid integer cutoff values.
    remaining = (instant(reservation['starts_at']) - now()).total_seconds()
    require(remaining > restaurant['cancellation_cutoff_minutes'] * 60, 'cutoff_passed', 409)


def changed(reservation, body, restaurants):
    require(reservation['status'] != 'cancelled', 'reservation_cancelled', 409)
    check_cutoff(reservation, restaurants[reservation['restaurant_id']])
    values = {k: reservation[k] for k in ('restaurant_id', 'table_id', 'starts_at_local', 'party_size')}
    values.update({k: body[k] for k in ('table_id', 'starts_at_local', 'party_size') if k in body})
    return {**reservation, **proposal(restaurants, values)}


def public_record(reservation):
    return {k: v for k, v in reservation.items() if k != 'user_id'}


def reference(value):
    require(type(value) is str and re.fullmatch(r'[A-Z0-9]{6,12}', value) is not None)
    return value
