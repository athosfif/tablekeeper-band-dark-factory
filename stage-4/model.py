"""Stage 4 state adds portable previews and applied closures to Stage 3."""
import stage3_model as inherited
from stage3_model import *
from planning import closure_interval, closure_overlap, solve, time_overlap


def empty_state():
    return {**inherited.empty_state(), 'schema_stage': 4, 'plans': [], 'closures': []}


def upgrade_four(state):
    state.update(schema_stage=4, plans=[], closures=[])
    return state


def fixture_state(body):
    return upgrade_four(inherited.fixture_state(body))


def plan_response(plan):
    return {k: clone(plan[k]) for k in ('plan_id', 'restaurant_revision', 'closure',
                                      'assignments', 'moved_count', 'unused_seats')}


def imported_state(envelope):
    try:
        if isinstance(envelope.get('state'), dict) and envelope['state'].get('schema_stage', 1) in (1, 2, 3):
            return upgrade_four(inherited.imported_state(envelope))
        require(envelope['track'] == 'tablekeeper' and type(envelope['format_version']) is int
                and envelope['format_version'] == 1)
        state = clone(envelope['state'])
        require(isinstance(state, dict) and set(state) == set(empty_state()))
        require(type(state['schema_stage']) is int and state['schema_stage'] == 4)
        require(isinstance(state['plans'], list) and isinstance(state['closures'], list))
        # Stage3 validates the common graph. A reassignment has the same immutable
        # history transition, expressed as its canonical changed-table equivalent.
        projection = {k: clone(state[k]) for k in inherited.empty_state()}
        projection['schema_stage'] = 3
        for entries in projection['histories'].values():
            for entry in entries:
                if entry['event'] != 'reassigned':
                    continue
                require(set(entry) == {'seq','at','event','changes','revision','accepted_terms','plan_id'})
                require(len(entry['changes']) == 1 and entry['changes'][0]['field'] == 'table_ids')
                entry.pop('plan_id')
                entry['event'] = 'changed'
                c = entry['changes'][0]
                if len(c['from']) == len(c['to']) == 1:
                    c.update(field='table_id', **{'from': c['from'][0], 'to': c['to'][0]})
        new_receipts, old_receipts = [], []
        for receipt in projection['receipts']:
            path = receipt.get('path', '')
            (new_receipts if re.fullmatch(r'/restaurants/[^/]+/replans(?:/[^/]+/apply)?|/series/[^/]+/amend', path)
             else old_receipts).append(receipt)
        projection['receipts'] = old_receipts
        inherited.imported_state({'track':'tablekeeper','format_version':1,'state':projection})
        restaurants = {r['id']: r for r in state['restaurants']}
        refs = {r['reference']: r for r in state['reservations']}
        users = {u['id'] for u in state['users']}

        def snapshot_record(record):
            current = refs[record['reference']]
            keys = set(public(current)) - {'table_id'}
            if len(record['table_ids']) == 1:
                keys.add('table_id')
            require(set(record) == keys)
            for key in ('reservation_id','reference','restaurant_id','created_at'):
                require(record[key] == current[key])
            require(type(record['revision']) is int and 1 <= record['revision'] <= current['revision'])
            require(record['status'] in ('confirmed','cancelled'))
            terms = record['accepted_terms']
            version = terms['policy_version']
            require(type(version) is int and 0 <= version <= len(state['policies'][record['restaurant_id']]))
            r = restaurants[record['restaurant_id']]
            wanted = policy_zero(r) if version == 0 else {
                k:v for k,v in state['policies'][r['id']][version - 1].items() if k != 'effective_from'}
            require(json_equal(terms, wanted))
            request = {k:record[k] for k in ('restaurant_id','starts_at_local','party_size','table_ids')}
            fields = booking_fields(state, request, terms)
            require(all(json_equal(record[k], v) for k,v in fields.items()))

        plans = {}
        for plan in state['plans']:
            require(set(plan) == {'plan_id','user_id','restaurant_id','restaurant_revision','closure',
                                  'assignments','moved_count','unused_seats','applied','basis'})
            pid = identifier(plan['plan_id'])
            require(pid not in plans and type(plan['applied']) is bool)
            plans[pid] = plan
            r = restaurants[plan['restaurant_id']]
            require(plan['user_id'] in r.get('manager_user_ids', []))
            require(type(plan['restaurant_revision']) is int and 0 <= plan['restaurant_revision'] <= state['restaurant_revisions'][r['id']])
            closure = plan['closure']
            require(json_equal(closure, closure_interval(closure)))
            require(closure['table_id'] in {t['id'] for t in r['tables']})
            basis = plan['basis']
            require(set(basis) == {'considered','fixed','closures'})
            require(all(isinstance(basis[k], list) for k in basis))
            seen = set()
            for category in ('considered','fixed'):
                for record in basis[category]:
                    snapshot_record(record)
                    require(record['reference'] not in seen and record['restaurant_id'] == r['id'] and record['status'] == 'confirmed')
                    seen.add(record['reference'])
                    intersects = time_overlap(instant(record['starts_at']),instant(record['ends_at']),instant(closure['from']),instant(closure['to']))
                    require(intersects == (category == 'considered'))
            for prior in basis['closures']:
                require(prior['restaurant_id'] == r['id'] and prior in state['closures'])
            solved = solve(r, closure, basis['considered'], basis['fixed'], basis['closures'])
            require(all(json_equal(plan[k], v) for k,v in solved.items()))
        applied = set()
        for closure in state['closures']:
            require(set(closure) == {'restaurant_id','table_id','from','to','plan_id'})
            plan = plans[closure['plan_id']]
            require(plan['applied'] and plan['plan_id'] not in applied and plan['restaurant_id'] == closure['restaurant_id'])
            require(json_equal(plan['closure'], {k:closure[k] for k in ('table_id','from','to')}))
            applied.add(plan['plan_id'])
            require(not any(closure_overlap(record, closure) for record in refs.values()))
        require(applied == {p['plan_id'] for p in plans.values() if p['applied']})
        for ref, entries in state['histories'].items():
            for entry in entries:
                if entry['event'] == 'reassigned':
                    plan = plans[entry['plan_id']]
                    require(plan['applied'] and plan['restaurant_id'] == refs[ref]['restaurant_id'])
                    assignment = next(a for a in plan['assignments'] if a['reference'] == ref)
                    original = next(b for b in plan['basis']['considered'] if b['reference'] == ref)
                    require(assignment['changed'] and entry['changes'] == [{'field':'table_ids','from':selected_tables(original),'to':assignment['table_ids']}])
                    require(json_equal(entry['accepted_terms'], original['accepted_terms']))
        scopes = set()
        for receipt in state['receipts']:
            require(set(receipt) == {'user_id','method','path','key','body','response'})
            require(receipt['user_id'] in users and receipt['method'] == 'POST')
            require(isinstance(receipt['key'],str) and 1 <= len(receipt['key']) <= 255)
            require(isinstance(receipt['body'],dict) and isinstance(receipt['response'],dict))
            scope = (receipt['user_id'],receipt['path'],receipt['key'])
            require(scope not in scopes)
            scopes.add(scope)
        for receipt in new_receipts:
            path, body, response, uid = (receipt[k] for k in ('path','body','response','user_id'))
            match = re.fullmatch(r'/restaurants/([^/]+)/replans(?:/([^/]+)/apply)?',path)
            if match:
                rid = unquote(match[1])
                plan = plans[response['plan_id']]
                require(plan['restaurant_id'] == rid and uid in restaurants[rid].get('manager_user_ids',[]))
                if match[2] is None:
                    require(plan['user_id'] == uid and json_equal(closure_interval(body),plan['closure']))
                    require(json_equal(response,plan_response(plan)))
                else:
                    require(unquote(match[2]) == plan['plan_id'] and plan['applied'])
                    require(set(response) == {'plan_id','restaurant_revision','reservations'})
                    require(response['restaurant_revision'] == plan['restaurant_revision'] + 1)
                    require([r['reference'] for r in response['reservations']] == [a['reference'] for a in plan['assignments']])
                    for record, assignment, original in zip(response['reservations'],plan['assignments'],plan['basis']['considered']):
                        snapshot_record(record)
                        require(record['table_ids'] == assignment['table_ids'])
                        require(record['revision'] == original['revision'] + int(assignment['changed']))
                        for key in ('starts_at','ends_at','accepted_terms','party_size','starts_at_local'):
                            require(json_equal(record[key],original[key]))
            else:
                match = re.fullmatch(r'/series/([^/]+)/amend',path)
                series = next(s for s in state['series'] if s['series_id'] == unquote(match[1]))
                require(series['user_id'] == uid and set(response) == {'series_id','revision','interval_weeks','occurrences'})
                require(response['series_id'] == series['series_id'] and response['interval_weeks'] == series['interval_weeks'])
                require(type(response['revision']) is int and 1 <= response['revision'] <= series['revision'])
                require(integer(body['expected_revision']) in (response['revision'], response['revision'] - 1))
                require(0 <= integer(body['from_index'],0) < len(series['occurrences']))
                clock_minutes(body['local_time'])
                require(len(response['occurrences']) == len(series['occurrences']))
                for item, current in zip(response['occurrences'],series['occurrences']):
                    require(set(item) == {'index','reference','exception','reservation'})
                    require(item['index'] == current['index'] and item['reference'] == current['reference'])
                    require(type(item['exception']) is bool and (not item['exception'] or current['exception']))
                    require(item['reservation']['reference'] == item['reference'])
                    snapshot_record(item['reservation'])
        return state
    except (APIError, legacy_model.APIError, KeyError, TypeError, ValueError, OverflowError, AttributeError, StopIteration):
        raise APIError(message='Invalid state export') from None
