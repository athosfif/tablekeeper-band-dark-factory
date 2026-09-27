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
    result['combinable'] = []
    for pair in field(body, 'combinable', list) if 'combinable' in body else []:
        require(type(pair) is list, 'malformed_request', 400)
        require(len(pair) == 2)
        ids = [identifier({'id': value}, 'id') for value in pair]
        require(len(set(ids)) == 2 and all(i in [t['id'] for t in result['tables']] for i in ids))
        require(not any(set(ids) == set(p) for p in result['combinable']))
        result['combinable'].append(ids)
    return result


def members(record):
    return record['table_ids'] if 'table_ids' in record else [record['table_id']]


def seating(restaurant, body):
    require(not ('table_id' in body and 'table_ids' in body))
    if 'table_ids' in body:
        values = field(body, 'table_ids', list)
        require(bool(values))
        ids = [identifier({'id': value}, 'id') for value in values]
    else:
        ids = [identifier(body, 'table_id')]
    require(len(set(ids)) == len(ids))
    require(len(ids) <= 2, 'combination_not_allowed')
    by_id = {t['id']: t for t in restaurant['tables']}
    require(all(i in by_id for i in ids), 'not_found', 404)
    if len(ids) == 2:
        pair = next((p for p in restaurant.get('combinable', []) if set(p) == set(ids)), None)
        require(pair is not None, 'combination_not_allowed')
        ids = list(pair)
    return ids, sum(by_id[i]['capacity'] for i in ids)


def seating_options(restaurant):
    for table in restaurant['tables']:
        yield {'table_ids': [table['id']], 'capacity': table['capacity']}
    by_id = {t['id']: t for t in restaurant['tables']}
    for pair in restaurant.get('combinable', []):
        yield {'table_ids': list(pair), 'capacity': sum(by_id[i]['capacity'] for i in pair)}


def proposal(restaurants, body):
    rid = identifier(body, 'restaurant_id')
    size = party(body)
    local = field(body, 'starts_at_local', str)
    require(rid in restaurants, 'not_found', 404)
    restaurant = restaurants[rid]
    ids, capacity = seating(restaurant, body)
    require(size <= capacity, 'party_exceeds_capacity')
    start, end = interval(restaurant, local)
    return {'restaurant_id': rid, 'table_ids': ids, **({'table_id': ids[0]} if len(ids) == 1 else {}), 'party_size': size,
            'starts_at_local': local, 'starts_at': start.isoformat(), 'ends_at': end.isoformat()}


def overlaps(a, b):
    return (a['restaurant_id'] == b['restaurant_id'] and bool(set(members(a)) & set(members(b)))
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
    values = {k: reservation[k] for k in ('restaurant_id', 'starts_at_local', 'party_size')}
    values.update({k: body[k] for k in ('table_id', 'table_ids', 'starts_at_local', 'party_size') if k in body})
    if 'table_id' not in body and 'table_ids' not in body:
        values['table_ids'] = members(reservation)
    unchanged = {k: v for k, v in reservation.items() if k not in ('table_id', 'table_ids')}
    return {**unchanged, **proposal(restaurants, values)}


def public_record(reservation):
    return {k: v for k, v in reservation.items() if k != 'user_id'}


def reference(value):
    require(type(value) is str and re.fullmatch(r'[A-Z0-9]{6,12}', value) is not None)
    return value
