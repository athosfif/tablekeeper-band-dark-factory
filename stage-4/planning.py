"""Bounded exhaustive seating optimization with deterministic lexicographic costs."""
from datetime import datetime
import re
from stage3_model import APIError, require, instant, selected_tables


def closure_interval(body):
    try:
        values = [body[k] for k in ('from', 'to')]
        for value in values:
            require(isinstance(value, str) and re.fullmatch(
                r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})', value))
            instant(value)
        require(instant(values[0]) < instant(values[1]))
        return {'table_id': body['table_id'], 'from': values[0], 'to': values[1]}
    except (KeyError, ValueError, TypeError, APIError):
        raise APIError(message='Invalid closure interval') from None


def time_overlap(start, end, other_start, other_end):
    return start < other_end and other_start < end


def closure_overlap(record, closure):
    return (record['status'] == 'confirmed' and record['restaurant_id'] == closure['restaurant_id']
            and closure['table_id'] in selected_tables(record)
            and time_overlap(instant(record['starts_at']), instant(record['ends_at']),
                             instant(closure['from']), instant(closure['to'])))


def solve(r, closure, considered, fixed, existing):
    """All option ranks are fixture order; search never mutates its input records."""
    require(len(r['tables']) <= 6 and len(r.get('combinable', [])) <= 4 and len(considered) <= 6,
            422, 'planning_limit')
    bookings = sorted(considered, key=lambda b: b['reference'])
    ids = {t['id']: 1 << n for n, t in enumerate(r['tables'])}
    options = [[t['id']] for t in r['tables']] + r.get('combinable', [])
    masks = [sum(ids[t] for t in option) for option in options]
    intervals = [(instant(b['starts_at']), instant(b['ends_at'])) for b in bookings]
    obstructions = [(sum(ids[t] for t in selected_tables(b)), instant(b['starts_at']), instant(b['ends_at']))
                    for b in fixed if b['status'] == 'confirmed']
    obstructions += [(ids[c['table_id']], instant(c['from']), instant(c['to'])) for c in existing + [closure]]
    choices = []
    for booking, (start, end) in zip(bookings, intervals):
        forbidden = 0
        for mask, other_start, other_end in obstructions:
            if time_overlap(start, end, other_start, other_end):
                forbidden |= mask
        valid = []
        for rank, (option, mask) in enumerate(zip(options, masks)):
            unused = sum(booking['accepted_terms']['capacities'][tid] for tid in option) - booking['party_size']
            if unused >= 0 and not mask & forbidden:
                changed = set(option) != set(selected_tables(booking))
                valid.append((int(changed), unused, rank, mask))
        if not valid:
            raise APIError(409, 'no_feasible_plan')
        choices.append(sorted(valid))
    count = len(bookings)
    conflicts = [[time_overlap(*intervals[i], *intervals[j]) for j in range(count)] for i in range(count)]
    best, best_ranks = None, None
    min_moves = [min(c[0] for c in choices[i]) for i in range(count)]
    min_unused = [min(c[1] for c in choices[i]) for i in range(count)]

    def visit(index, moved, unused, ranks, occupied):
        nonlocal best, best_ranks
        lower = (moved + sum(min_moves[index:]), unused + sum(min_unused[index:]))
        if best is not None and (lower[0] > best[0] or lower[0] == best[0] and lower[1] > best[1]):
            return
        if index == count:
            score = (moved, unused, tuple(ranks))
            if best is None or score < best:
                best, best_ranks = score, list(ranks)
            return
        for changed, waste, rank, mask in choices[index]:
            if any(conflicts[index][j] and mask & previous for j, previous in enumerate(occupied)):
                continue
            visit(index + 1, moved + changed, unused + waste, ranks + [rank], occupied + [mask])

    visit(0, 0, 0, [], [])
    if best is None:
        raise APIError(409, 'no_feasible_plan')
    return {'assignments': [{'reference': b['reference'], 'table_ids': list(options[rank]),
                             'changed': set(options[rank]) != set(selected_tables(b))}
                            for b, rank in zip(bookings, best_ranks)],
            'moved_count': best[0], 'unused_seats': best[1]}
