"""Independent exhaustive closure objective, derived before Stage4 source review.

Not service code. Operates on public fixture, reservation and proposed closure values.
No state exports, tokens, credentials or service implementation imports.
"""
from datetime import datetime
import itertools
import unittest

def instant(text):
    result=datetime.fromisoformat(text.replace('Z','+00:00'))
    assert result.utcoffset() is not None
    return result.timestamp()

def overlaps(a,b):return a[0]<b[1] and b[0]<a[1]

def solve(fixture,records,closure,existing_closures=()):
    """Return exact objective + assignments, or None; no mutation of arguments."""
    options=[(t['id'],) for t in fixture['tables']]+[tuple(p) for p in fixture.get('combinable',[])]
    span=(instant(closure['from']),instant(closure['to']))
    bookings=[r for r in records if r['status']=='confirmed' and r['restaurant_id']==fixture['id']]
    intervals={r['reference']:(instant(r['starts_at']),instant(r['ends_at'])) for r in bookings}
    considered=sorted([r for r in bookings if overlaps(intervals[r['reference']],span)],key=lambda r:r['reference'])
    fixed=[r for r in bookings if not overlaps(intervals[r['reference']],span)]
    closures=[*existing_closures,closure]
    def selected(row):return frozenset(row.get('table_ids',[row.get('table_id')]))
    choices=[]
    for row in considered:
        caps=row['accepted_terms']['capacities'];interval=intervals[row['reference']]
        viable=[]
        for rank,option in enumerate(options):
            seats=sum(caps[t] for t in option)
            if seats<row['party_size']:continue
            if any(c['table_id'] in option and overlaps(interval,(instant(c['from']),instant(c['to']))) for c in closures):continue
            if any(set(option)&selected(r) and overlaps(interval,intervals[r['reference']]) for r in fixed):continue
            viable.append((rank,option,seats-row['party_size'],frozenset(option)!=selected(row)))
        choices.append(viable)
    best=None
    # Deliberately simple enumeration differs from an optimizing service solver.
    for assignment in itertools.product(*choices):
        if any(set(assignment[i][1])&set(assignment[j][1]) and overlaps(intervals[considered[i]['reference']],intervals[considered[j]['reference']])
               for i in range(len(considered)) for j in range(i)):
            continue
        objective=(sum(a[3] for a in assignment),sum(a[2] for a in assignment),tuple(a[0] for a in assignment))
        rows=[{'reference':r['reference'],'table_ids':list(a[1]),'changed':a[3]} for r,a in zip(considered,assignment)]
        if best is None or objective<best['objective']:
            best={'objective':objective,'assignments':rows,'moved_count':objective[0],'unused_seats':objective[1]}
    return best

class OracleSanity(unittest.TestCase):
    def setUp(self):
        self.f={'id':'r','tables':[{'id':'a'},{'id':'b'},{'id':'c'}],'combinable':[['c','b']]}
        self.c={'table_id':'a','from':'2040-01-01T18:00:00Z','to':'2040-01-01T20:00:00Z'}

    def booking(self,ref,table,party=2,start='18:00',end='19:00',caps=None):
        return dict(reference=ref,restaurant_id='r',status='confirmed',table_ids=[table],party_size=party,
                    starts_at='2040-01-01T'+start+':00Z',ends_at='2040-01-01T'+end+':00Z',
                    accepted_terms={'capacities':caps or {'a':2,'b':2,'c':6}})

    def test_changed_count_precedes_unused_seats(self):
        r=self.booking('Z00000','c')
        result=solve(self.f,[r],self.c)
        self.assertEqual(result['objective'],(0,4,(2,)))

    def test_unused_then_fixture_rank(self):
        r=self.booking('Z00000','a',caps={'a':2,'b':3,'c':3})
        self.assertEqual(solve(self.f,[r],self.c)['objective'],(1,1,(1,)))

    def test_reference_order_and_half_open(self):
        rows=[self.booking('Z00000','a',start='19:00',end='20:00'),self.booking('A00000','a')]
        result=solve(self.f,rows,self.c)
        self.assertEqual(result['objective'],(2,0,(1,1)))
        self.assertEqual([r['reference'] for r in result['assignments']],['A00000','Z00000'])

    def test_fixed_booking_outside_proposed_interval_still_matters(self):
        c=dict(self.c,to='2040-01-01T18:30:00Z')
        rows=[self.booking('A00000','a',end='20:00'),self.booking('B00000','b',start='19:00',end='20:00')]
        result=solve(self.f,rows,c)
        self.assertEqual(result['assignments'],[{'reference':'A00000','table_ids':['c'],'changed':True}])

    def test_no_plan_and_empty_plan(self):
        row=self.booking('A00000','a',party=20)
        self.assertIsNone(solve(self.f,[row],self.c))
        self.assertEqual(solve(self.f,[],self.c)['objective'],(0,0,()))

if __name__=='__main__':unittest.main(verbosity=2)
