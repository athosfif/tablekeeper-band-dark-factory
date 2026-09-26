"""Specification-derived series amendments and operator/series interactions."""
import copy
import datetime as dt
import unittest
import reviewer_inherited as api
from reviewer_replan_checks import ReplanChecks,closure_fixture,request

class SeriesAmendChecks(unittest.TestCase):
    reset=ReplanChecks.reset;login=ReplanChecks.login;err=ReplanChecks.err;listing=ReplanChecks.listing
    body=ReplanChecks.body;book=ReplanChecks.book;policy=ReplanChecks.policy;publish=ReplanChecks.publish
    history=ReplanChecks.history;patch=ReplanChecks.patch;adopt=ReplanChecks.adopt;series=ReplanChecks.series
    burst=ReplanChecks.burst;closure=ReplanChecks.closure;preview=ReplanChecks.preview;apply=ReplanChecks.apply;revision=ReplanChecks.revision

    def setUp(self):
        self.seed=closure_fixture();self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)];self.counter=0
        self.anchor=self.book('t0',party=2);self.adoptbody,self.agreement=self.adopt(self.anchor,count=5)

    def amend(self,changes=None,key='amend'):
        body=changes if changes is not None else dict(expected_revision=1,from_index=0,local_time='19:00')
        return request('POST','/series/'+self.agreement['series_id']+'/amend',body,self.tokens[0],key)

    def test_amend_01_validation_auth_and_stale_precedence(self):
        path='/series/'+self.agreement['series_id']+'/amend'
        body=dict(expected_revision=1,from_index=0,local_time='19:00')
        self.err('POST',path,body,401,'unauthenticated',token=None)
        self.err('POST',path,body,404,'not_found',token=self.tokens[1])
        self.err('POST','/series/missing/amend',body,404,'not_found')
        before=self.series(self.agreement)[1]
        for field,values in [('expected_revision',[0,-1,True,'1',1.5]),('from_index',[-1,5,False,'0',.5]),('local_time',['9:00','24:00','19:60','19:00Z','19:00:00',None])]:
            for value in values:self.err('POST',path,dict(body,**{field:value}),422,'validation_failed',key='reusable')
        for field in body:
            b=dict(body);del b[field];self.err('POST',path,b,422,'validation_failed',key='reusable')
        self.err('POST',path,dict(body,expected_revision=2,local_time='03:00'),409,'stale_revision')
        self.assertEqual(self.series(self.agreement)[1],before)
        self.assertEqual(self.amend(body,'reusable')[0],201)

    def test_amend_02_skip_exceptions_cancelled_and_original_dates(self):
        rows=[o['reservation'] for o in self.agreement['occurrences']]
        shifted=(dt.date.fromisoformat(rows[1]['starts_at_local'][:10])+dt.timedelta(days=1)).isoformat()+'T18:00'
        self.assertEqual(self.patch(rows[1],{'starts_at_local':shifted})[0],200)
        request('POST','/reservations/'+rows[2]['reference']+'/cancel',{},self.tokens[0])
        before=self.series(self.agreement)[1];hist={o['reference']:self.history(o['reservation']) for o in before['occurrences']}
        body=dict(expected_revision=before['revision'],from_index=1,local_time='19:00')
        status,result=self.amend(body);self.assertEqual(status,201);self.assertEqual(result['revision'],before['revision']+1)
        self.assertEqual([o['exception'] for o in result['occurrences']],[False,True,False,False,False])
        for i,o in enumerate(result['occurrences']):
            prior=before['occurrences'][i]['reservation'];row=o['reservation']
            for field in ['reference','reservation_id','created_at','party_size','table_ids']:self.assertEqual(row[field],prior[field])
            if i in [3,4]:
                self.assertEqual(row['starts_at_local'],rows[i]['starts_at_local'][:10]+'T19:00')
                self.assertEqual(row['revision'],prior['revision']+1)
                self.assertEqual(len(self.history(row)),len(hist[o['reference']])+1)
            else:self.assertEqual(row,prior);self.assertEqual(self.history(row),hist[o['reference']])
        self.assertEqual(self.revision(),5)
        self.patch(rows[3],{'party_size':1})
        self.assertEqual(self.amend(body),(200,result))

    def test_amend_03_noop_and_empty_sets_preserve_revisions(self):
        before=self.series(self.agreement)[1];revision=self.revision()
        status,result=self.amend(dict(expected_revision=1,from_index=0,local_time='18:00'),'noop')
        self.assertEqual((status,result),(201,before));self.assertEqual(self.revision(),revision)
        for o in before['occurrences']:request('POST','/reservations/'+o['reference']+'/cancel',{},self.tokens[0])
        cancelled=self.series(self.agreement)[1];revision=self.revision()
        body=dict(expected_revision=cancelled['revision'],from_index=0,local_time='20:00')
        self.assertEqual(self.amend(body,'empty'),(201,cancelled));self.assertEqual(self.revision(),revision)
        self.assertEqual(self.amend(body,'empty'),(200,cancelled))

    def test_amend_04_nonoccupancy_precedes_occupancy_and_atomicity(self):
        rows=[o['reservation'] for o in self.agreement['occurrences']]
        # First eligible booking's new time overlaps an unlisted later booking.
        self.book('t0',clock='20:00',party=2,key='blocker')
        # Later occurrence's selected new policy instead disallows every opening time.
        self.publish(self.policy(rows[2]['starts_at_local'][:10],opening_hours=[]))
        before=self.series(self.agreement)[1];hist=[self.history(r) for r in rows];revision=self.revision()
        body=dict(expected_revision=1,from_index=0,local_time='19:00')
        path='/series/'+self.agreement['series_id']+'/amend'
        self.err('POST',path,body,422,'outside_opening_hours',key='failed')
        self.assertEqual(self.series(self.agreement)[1],before);self.assertEqual(self.revision(),revision)
        self.assertEqual([self.history(r) for r in rows],hist)
        self.publish(self.policy(rows[2]['starts_at_local'][:10]),'repair-policy')
        self.err('POST',path,body,409,'table_unavailable',key='failed')
        # Corrected body under the failed key is first use, not conflicting reuse.
        status,_=self.amend(dict(body,local_time='18:00'),'failed');self.assertEqual(status,201)

    def test_amend_05_concurrent_expected_revision(self):
        body=dict(expected_revision=1,from_index=0,local_time='19:00')
        replies=self.burst(lambda i:self.amend(body,'concurrent'+str(i)))
        self.assertEqual(sum(s==201 for s,v in replies),1)
        self.assertEqual(sum(s==409 and v['error']['code']=='stale_revision' for s,v in replies),49)
        current=self.series(self.agreement)[1];self.assertEqual(current['revision'],2);self.assertEqual(self.revision(),3)
        for o in current['occurrences']:
            self.assertEqual(o['reservation']['revision'],2);self.assertFalse(o['exception']);self.assertEqual(len(self.history(o['reservation'])),2)

    def test_amend_06_plan_moves_preserve_exceptions_and_aggregate_once(self):
        rows=[o['reservation'] for o in self.agreement['occurrences']]
        self.patch(rows[1],{'party_size':1})
        before=self.series(self.agreement)[1]
        start=rows[0]['starts_at_local']+':00+00:00';end=rows[1]['starts_at_local'][:10]+'T20:00:00+00:00'
        status,plan=self.preview({'table_id':'t0','from':start,'to':end});self.assertEqual(status,201)
        self.assertEqual(plan['moved_count'],2)
        status,_=self.apply(plan);self.assertEqual(status,201)
        changed=self.series(self.agreement)[1];self.assertEqual(changed['revision'],before['revision']+1)
        self.assertEqual([o['exception'] for o in changed['occurrences']],[False,True,False,False,False])
        for old,new in zip(before['occurrences'],changed['occurrences']):
            self.assertEqual(old['reference'],new['reference']);self.assertEqual(old['index'],new['index'])
            for field in ['starts_at_local','starts_at','ends_at','accepted_terms','created_at']:self.assertEqual(old['reservation'][field],new['reservation'][field])
        body=dict(expected_revision=changed['revision'],from_index=0,local_time='19:00')
        status,result=self.amend(body);self.assertEqual(status,201)
        for i,o in enumerate(result['occurrences']):
            self.assertEqual(o['reservation']['starts_at_local'],rows[i]['starts_at_local'][:10]+('T18:00' if i==1 else 'T19:00'))
            self.assertEqual(o['reservation']['table_ids'],changed['occurrences'][i]['reservation']['table_ids'])

    def test_amend_07_calendar_gap_rolls_back_all_occurrences(self):
        self.seed['restaurants'][0].update(timezone='Europe/Berlin',opening_hours=[dict(weekday='sun',opens='00:00',closes='06:00')])
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        anchor=self.book('t0',day='2030-03-24',clock='01:30',party=2)
        _,self.agreement=self.adopt(anchor,count=3)
        before=self.series(self.agreement)[1];hist=[self.history(o['reservation']) for o in before['occurrences']]
        revision=self.revision()
        body=dict(expected_revision=1,from_index=0,local_time='02:30')
        status,error=self.amend(body,'gap')
        self.assertEqual((status,error['error']['code']),(422,'invalid_local_time'))
        self.assertEqual(self.series(self.agreement)[1],before)
        self.assertEqual([self.history(o['reservation']) for o in before['occurrences']],hist)
        self.assertEqual(self.revision(),revision)
        status,result=self.amend(dict(body,local_time='03:30'),'gap');self.assertEqual(status,201)
        self.assertEqual(result['revision'],2)
        for o in result['occurrences']:
            self.assertTrue(o['reservation']['starts_at_local'].endswith('T03:30'));self.assertFalse(o['exception'])
