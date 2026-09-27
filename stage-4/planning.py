"""Exact bounded seating optimization; previews never mutate operational state."""
from copy import deepcopy
import re
import secrets

from domain import available, members, public_record
from ledger import bump_restaurant, commit_changes
from timekeeping import instant
from validation import identifier, require


def closure_body(body, restaurant):
    table = identifier(body, 'table_id')
    require(any(t['id'] == table for t in restaurant['tables']), 'not_found', 404)
    parsed = []
    for key in ('from', 'to'):
        value = body.get(key)
        require(type(value) is str and re.fullmatch(
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})', value))
        try:
            normalized = value.replace('t', 'T').replace('z', 'Z')
            parsed.append(instant(normalized))
        except (ValueError, OverflowError):
            require(False)
    require(parsed[0] < parsed[1])
    return {'table_id': table, 'from': body['from'].replace('t', 'T').replace('z', 'Z'),
            'to': body['to'].replace('t', 'T').replace('z', 'Z')}


def public_plan(plan):
    return {k: deepcopy(v) for k, v in plan.items() if k not in ('restaurant_id', 'applied')}


def solve(state, rid, closure):
    restaurant = state['restaurants'][rid]
    begin, end = instant(closure['from']), instant(closure['to'])
    records = sorted((r for r in state['reservations'].values()
                      if r['restaurant_id'] == rid and r['status'] == 'confirmed'
                      and instant(r['starts_at']) < end and begin < instant(r['ends_at'])),
                     key=lambda r: r['reference'])
    require(len(restaurant['tables']) <= 6 and len(restaurant['combinable']) <= 4 and len(records) <= 6,
            'planning_limit')
    options = [[t['id']] for t in restaurant['tables']] + restaurant['combinable']
    bits = {t['id']: 1 << i for i, t in enumerate(restaurant['tables'])}
    masks = [sum(bits[t] for t in option) for option in options]
    refs = {r['reference'] for r in records}
    closures = [*state['closures'].values(), {'restaurant_id': rid, **closure}]
    domains = []
    for record in records:
        domain = []
        capacities = record['accepted_terms']['capacities']
        for rank, option in enumerate(options):
            capacity = sum(capacities[t] for t in option)
            if capacity >= record['party_size'] and available(
                    {**record, 'table_ids': option}, state['reservations'], refs, closures):
                domain.append((rank, int(set(option) != set(members(record))), capacity - record['party_size']))
        require(domain, 'no_feasible_plan', 409)
        domains.append(domain)
    # Date arithmetic and occupancy scans stay out of the combinatorial search.
    conflicts = [[instant(a['starts_at']) < instant(b['ends_at']) and
                  instant(b['starts_at']) < instant(a['ends_at']) for b in records] for a in records]
    lower_moved, lower_unused = [0] * (len(records) + 1), [0] * (len(records) + 1)
    for i in range(len(records) - 1, -1, -1):
        lower_moved[i] = lower_moved[i + 1] + min(o[1] for o in domains[i])
        lower_unused[i] = lower_unused[i + 1] + min(o[2] for o in domains[i])
    best = None

    def search(i, moved, unused, ranks):
        nonlocal best
        if best is not None and (moved + lower_moved[i], unused + lower_unused[i]) > best[:2]:
            return
        if i == len(records):
            score = (moved, unused, tuple(ranks))
            if best is None or score < best:
                best = score
            return
        for rank, delta, spare in domains[i]:
            if all(not conflicts[i][j] or not (masks[rank] & masks[other]) for j, other in enumerate(ranks)):
                search(i + 1, moved + delta, unused + spare, [*ranks, rank])

    search(0, 0, 0, [])
    require(best is not None, 'no_feasible_plan', 409)
    assignments = [{'reference': record['reference'], 'table_ids': list(options[rank]),
                    'changed': set(members(record)) != set(options[rank])}
                   for record, rank in zip(records, best[2])]
    return assignments, best[0], best[1]


def preview(state, rid, body):
    closure = closure_body(body, state['restaurants'][rid])
    assignments, moved, unused = solve(state, rid, closure)
    pid = 'plan_' + secrets.token_hex(16)
    while pid in state['plans']:
        pid = 'plan_' + secrets.token_hex(16)
    plan = {'plan_id': pid, 'restaurant_id': rid, 'applied': False,
            'restaurant_revision': state['restaurant_revisions'][rid], 'closure': closure,
            'assignments': assignments, 'moved_count': moved, 'unused_seats': unused}
    state['plans'][pid] = plan
    return public_plan(plan)


def apply_plan(state, rid, pid):
    plan = state['plans'].get(pid)
    require(plan is not None and plan['restaurant_id'] == rid, 'not_found', 404)
    require(not plan['applied'], 'plan_already_applied', 409)
    require(plan['restaurant_revision'] == state['restaurant_revisions'][rid], 'stale_plan', 409)
    candidates = []
    for assignment in plan['assignments']:
        record = state['reservations'][assignment['reference']]
        if assignment['changed']:
            record = {k: v for k, v in record.items() if k not in ('table_ids', 'table_id')}
            ids = list(assignment['table_ids'])
            record.update(table_ids=ids, revision=record['revision'] + 1)
            if len(ids) == 1:
                record['table_id'] = ids[0]
        candidates.append(record)
    commit_changes(state, candidates, 'reassigned', mark_exceptions=False, bump=False, plan_id=pid)
    state['closures'][pid] = {'restaurant_id': rid, **deepcopy(plan['closure'])}
    plan['applied'] = True
    bump_restaurant(state, rid)
    return {'plan_id': pid, 'restaurant_revision': state['restaurant_revisions'][rid],
            'reservations': [public_record(r) for r in candidates]}
