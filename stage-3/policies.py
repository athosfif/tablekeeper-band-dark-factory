"""Immutable published policies and date-based selection of complete terms."""
from copy import deepcopy

from timekeeping import calendar_date, clock_time, WEEKDAYS
from validation import APIError, field, party, require, fail

RULE_FIELDS = ('slot_minutes', 'reservation_duration_minutes', 'cancellation_cutoff_minutes', 'opening_hours')


def bounded_integer(value, minimum=1, maximum=None):
    # JSON integers are values, not a lexical restriction on 4 versus 4.0.
    if minimum == 0 and type(value) is not bool and value == 0:
        return 0
    number = party({'party_size': value})
    require(number >= minimum and (maximum is None or number <= maximum))
    return number


def base_terms(restaurant):
    return deepcopy({'policy_version': 0, **{k: restaurant[k] for k in RULE_FIELDS},
                     'capacities': {t['id']: t['capacity'] for t in restaurant['tables']}})


def policy_body(body, restaurant):
    """All errors inside a complete policy have its endpoint-specific 422 code."""
    try:
        effective = field(body, 'effective_from', str)
        calendar_date(effective)
        policy = {'effective_from': effective}
        for key, minimum, maximum in [('slot_minutes', 1, 1440),
                                       ('reservation_duration_minutes', 1, 1440),
                                       ('cancellation_cutoff_minutes', 0, 10080)]:
            policy[key] = bounded_integer(body.get(key), minimum, maximum)
        policy['opening_hours'] = []
        for entry in field(body, 'opening_hours', list):
            require(type(entry) is dict)
            day = field(entry, 'weekday', str)
            require(day in WEEKDAYS and day not in [h['weekday'] for h in policy['opening_hours']])
            opens, closes = field(entry, 'opens', str), field(entry, 'closes', str)
            require(clock_time(opens) < clock_time(closes))
            policy['opening_hours'].append({'weekday': day, 'opens': opens, 'closes': closes})
        capacities = field(body, 'capacities', dict)
        require(set(capacities) == {t['id'] for t in restaurant['tables']})
        policy['capacities'] = {tid: bounded_integer(value, 1, 100) for tid, value in capacities.items()}
        return policy
    except APIError:
        fail('validation_failed')


def terms_of(policy):
    return deepcopy({k: v for k, v in policy.items() if k != 'effective_from'})


def selected_terms(restaurant, local_date, policies=()):
    eligible = [p for p in policies if p['effective_from'] <= local_date]
    return terms_of(max(eligible, key=lambda p: (p['effective_from'], p['policy_version']))) if eligible else base_terms(restaurant)


def effective_config(restaurant, terms):
    return {**restaurant, **{k: terms[k] for k in RULE_FIELDS},
            'tables': [{**t, 'capacity': terms['capacities'][t['id']]} for t in restaurant['tables']]}
