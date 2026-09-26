"""Populated actual earlier-service upgrades and policy edge cases; no app imports."""
import copy
import datetime as dt
import os
import unittest
from urllib.parse import quote
import reviewer_inherited as api
from reviewer_policy_checks import PolicyChecks, policy_fixture

request=api.request
OLD1=os.environ['REVIEW_OLD'];OLD2=os.environ['REVIEW_OLD2']

class UpgradeChecks(unittest.TestCase):
    reset=PolicyChecks.reset;login=PolicyChecks.login;err=PolicyChecks.err
    listing=PolicyChecks.listing;body=PolicyChecks.body;book=PolicyChecks.book
    policy=PolicyChecks.policy;publish=PolicyChecks.publish;history=PolicyChecks.history
    patch=PolicyChecks.patch;adopt=PolicyChecks.adopt;series=PolicyChecks.series
    burst=PolicyChecks.burst

    def setUp(self):
        self.seed=policy_fixture();self.reset(self.seed)
        self.tokens=[self.login(i) for i in range(2)]

    def test_upgrade_01_populated_actual_stages1_and2(self):
        for stage,base in [(1,OLD1),(2,OLD2)]:
            with self.subTest(stage=stage):
                seed=policy_fixture();self.reset(seed,base=base)
                token=self.login(base=base);second=self.login(base=base)
                body=self.body()
                if stage==2:body.pop('table_id');body['table_ids']=['t1','t2']
                body['ignored']={'persist':[True,1,None]}
                status,receipt=request('POST','/reservations',body,token,'old-create',base=base);self.assertEqual(status,201)
                cancelled=request('POST','/reservations',self.body('t3',clock='20:00'),token,'old-cancelled',base=base)[1]
                request('POST','/reservations/'+cancelled['reference']+'/cancel',{},token,base=base)
                batchbody={'moves':[{'reference':receipt['reference'],'starts_at_local':api.FUTURE+'T19:00'}]}
                status,batch=request('POST','/reservation-moves',batchbody,token,'old-batch',base=base);self.assertEqual(status,201)
                failed=self.body('t3',party=100)
                self.assertEqual(request('POST','/reservations',failed,token,'old-failed',base=base)[0],422)
                before=request('GET','/reservations',token=token,base=base)[1]['reservations']
                snapshot=request('GET','/_test/export',base=base)[1]
                # Mutation after export cannot alter the independently held snapshot.
                request('POST','/reservations/'+receipt['reference']+'/cancel',{},token,base=base)
                for repeat in range(2):
                    self.reset(base=api.DEST);displaced=self.login(base=api.DEST)
                    self.assertEqual(request('POST','/_test/import',snapshot,base=api.DEST)[0],204)
                    self.assertEqual(request('GET','/reservations',token=displaced,base=api.DEST)[0],401)
                    for session in [token,second]:
                        rows=request('GET','/reservations',token=session,base=api.DEST)[1]['reservations']
                        self.assertEqual([{k:r[k] for k in old} for r,old in zip(rows,before)],before)
                        self.assertEqual(len(rows),len(before))
                        for row in rows:
                            self.assertGreaterEqual(row['revision'],1);self.assertEqual(row['accepted_terms']['policy_version'],0)
                    self.assertEqual(request('POST','/reservations',body,token,'old-create',base=api.DEST),(200,receipt))
                    self.assertEqual(request('POST','/reservation-moves',batchbody,token,'old-batch',base=api.DEST),(200,batch))
                    self.assertEqual(request('POST','/auth/login',{'email':'reviewer0@example.test','password':api.PASSWORD},base=api.DEST)[0],200)
                    adopted_body=dict(anchor_reference=receipt['reference'],count=3,interval_weeks=1)
                    status,series=request('POST','/series',adopted_body,token,'imported-adopt',base=api.DEST);self.assertEqual(status,201)
                    self.assertEqual(len(series['occurrences']),3)
                    self.assertEqual(request('POST','/reservations',body,token,'old-create',base=api.DEST),(200,receipt))
                    self.assertEqual(request('POST','/reservations',self.body('t3'),token,'old-failed',base=api.DEST)[0],201)

    def test_upgrade_02_stage3_snapshot_preserves_policy_history_series_receipts(self):
        anchor=self.book();original=self.body();body,series=self.adopt(anchor,count=4)
        policybody=self.policy(reservation_duration_minutes=60)
        published=self.publish(policybody)
        one=series['occurrences'][1]['reservation'];two=series['occurrences'][2]['reservation']
        moves={'moves':[{'reference':one['reference'],'party_size':3}]}
        status,batch=request('POST','/reservation-moves',moves,self.tokens[0],'moved');self.assertEqual(status,201)
        request('POST','/reservations/'+two['reference']+'/cancel',{},self.tokens[0])
        expected=self.series(series)[1];histories={o['reference']:self.history(o['reservation']) for o in expected['occurrences']}
        current=self.listing();snapshot=request('GET','/_test/export')[1]
        self.patch(anchor,{'party_size':2})
        for repeat in range(2):
            self.reset(base=api.DEST);displaced=self.login(base=api.DEST)
            self.assertEqual(request('POST','/_test/import',snapshot,base=api.DEST)[0],204)
            self.assertEqual(request('GET','/series/'+series['series_id'],token=self.tokens[0],base=api.DEST),(200,expected))
            self.assertEqual(request('GET','/reservations',token=self.tokens[0],base=api.DEST)[1]['reservations'],current)
            for ref,hist in histories.items():self.assertEqual(request('GET','/reservations/'+ref+'/history',token=self.tokens[0],base=api.DEST)[1]['entries'],hist)
            for path,b,k,response in [('/reservations',original,'book',anchor),('/series',body,'adopt',series),('/reservation-moves',moves,'moved',batch),('/restaurants/r/policies',policybody,'policy',published)]:
                self.assertEqual(request('POST',path,b,self.tokens[0],k,base=api.DEST),(200,response))
            self.assertEqual(request('GET','/reservations',token=displaced,base=api.DEST)[0],401)
            for bad in [{},dict(snapshot,track='bad'),dict(snapshot,format_version=True),dict(snapshot,state={})]:
                self.assertEqual(request('POST','/_test/import',bad,base=api.DEST)[0],422)
                self.assertEqual(request('GET','/series/'+series['series_id'],token=self.tokens[0],base=api.DEST),(200,expected))
            self.assertEqual(request('POST','/_test/import',raw=b'{',base=api.DEST)[0],400)

    def test_policy_extra_01_old_accepted_cutoff_precedes_new_rules(self):
        clock=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=20)).replace(second=0,microsecond=0)
        # Avoid a midnight-only edge in this timed scenario; choose the next daytime start.
        if clock.hour==23:clock+=dt.timedelta(hours=2)
        day=clock.date().isoformat();local=clock.strftime('%H:%M')
        seed=policy_fixture();r=seed['restaurants'][0]
        r.update(slot_minutes=1,reservation_duration_minutes=1,cancellation_cutoff_minutes=0,
                 opening_hours=[dict(weekday=d,opens='00:00',closes='23:59') for d in api.fixture()['restaurants'][0]['opening_hours'] for d in [d['weekday']]])
        self.seed=seed;self.reset(seed);self.tokens=[self.login(i) for i in range(2)]
        a=self.book(day=day,clock=local);b=self.book('t2',day=day,clock=local,key='b')
        self.publish(self.policy(day,cancellation_cutoff_minutes=10080))
        self.assertEqual(request('POST','/reservations/'+a['reference']+'/cancel',{},self.tokens[0])[0],200)
        status,new=self.patch(b,{'party_size':3});self.assertEqual(status,200)
        self.assertEqual(new['accepted_terms']['cancellation_cutoff_minutes'],10080)
        self.err('PATCH','/reservations/'+b['reference'],{'party_size':False},409,'cutoff_passed')
        self.err('PATCH','/reservations/'+b['reference'],{'expected_revision':1,'party_size':False},409,'stale_revision')
        self.err('POST','/reservations/'+b['reference']+'/cancel',{},409,'cutoff_passed')
        self.publish(self.policy(day,cancellation_cutoff_minutes=0),'less-restrictive')
        self.err('PATCH','/reservations/'+b['reference'],{'party_size':2},409,'cutoff_passed')

    def test_policy_extra_02_concurrent_distinct_versions_and_paths(self):
        body=self.policy()
        replies=self.burst(lambda i:request('POST','/restaurants/r/policies',dict(body,note={'i':i}),self.tokens[0],'unique'+str(i)))
        self.assertTrue(all(s==201 for s,v in replies))
        self.assertEqual(sorted(v['policy_version'] for s,v in replies),list(range(1,51)))
        self.assertEqual([p['policy_version'] for p in request('GET','/restaurants/r/policies')[1]['policies']],list(range(1,51)))
        # A used body changed only in an ignored field must still conflict before validation.
        self.err('POST','/restaurants/r/policies',{'note':True},409,'idempotency_key_reuse',key='unique0')
        seed=policy_fixture();seed['restaurants'][0]['id']='r/雪%2F?# space';self.seed=seed
        self.reset(seed);self.tokens=[self.login(i) for i in range(2)]
        path='/restaurants/'+quote(seed['restaurants'][0]['id'],safe='')+'/policies'
        status,p=request('POST',path,self.policy(),self.tokens[0],'encoded');self.assertEqual(status,201)
        self.assertEqual(request('GET',path),(200,{'policies':[p]}))

    def test_series_extra_01_first_error_and_cancelled_anchor(self):
        anchor=self.book();body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
        later=(dt.date.fromisoformat(api.FUTURE)+dt.timedelta(days=14)).isoformat()
        self.publish(self.policy(later,capacities={'t0':2,'t1':1,'t2':8,'t3':8}))
        earlier=(dt.date.fromisoformat(api.FUTURE)+dt.timedelta(days=7)).isoformat()
        self.book(day=earlier,key='blocker')
        before=self.listing()
        # First failing occurrence1 occupancy wins over occurrence2 capacity.
        self.err('POST','/series',body,409,'table_unavailable',key='first')
        self.assertEqual(self.listing(),before)
        request('POST','/reservations/'+anchor['reference']+'/cancel',{},self.tokens[0])
        self.err('POST','/series',body,409,'reservation_cancelled',key='cancelled')

    def test_series_extra_02_new_york_calendar_gap_and_fold(self):
        seed=policy_fixture();seed['restaurants'][0].update(timezone='America/New_York',opening_hours=[dict(weekday='sun',opens='00:00',closes='06:00')])
        self.seed=seed;self.reset(seed);self.tokens=[self.login(i) for i in range(2)]
        anchor=self.book(day='2030-03-03',clock='02:30')
        self.err('POST','/series',dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1),422,'invalid_local_time',key='gap')
        self.assertEqual(self.listing(),[anchor])
        fall=self.book(day='2030-10-27',clock='01:30',key='fall')
        _,series=self.adopt(fall,count=2,key='fall-series')
        row=series['occurrences'][1]['reservation']
        self.assertEqual(row['starts_at_local'],'2030-11-03T01:30');self.assertTrue(row['starts_at'].endswith('-04:00'))
        self.assertEqual(row['ends_at'][11:16],'02:00');self.assertTrue(row['ends_at'].endswith('-05:00'))

    def test_policy_extra_03_scopes_ignored_body_and_pair_capacity(self):
        seed=policy_fixture();seed['restaurants'][0]['manager_user_ids']=['u0','u1']
        other=copy.deepcopy(seed['restaurants'][0]);other['id']='other';seed['restaurants'][1]=other
        self.seed=seed;self.reset(seed);self.tokens=[self.login(i) for i in range(2)]
        body=self.policy();body['ignored']={'number':1,'flag':False}
        receipt=request('POST','/restaurants/r/policies',body,self.tokens[0],'scoped')[1]
        equivalent=copy.deepcopy(body);equivalent['ignored']['number']=1.0
        self.assertEqual(request('POST','/restaurants/r/policies',equivalent,self.tokens[0],'scoped'),(200,receipt))
        different=copy.deepcopy(body);different['ignored']['number']=True
        self.err('POST','/restaurants/r/policies',different,409,'idempotency_key_reuse',key='scoped')
        self.assertEqual(request('POST','/restaurants/r/policies',body,self.tokens[1],'scoped')[0],201)
        self.assertEqual(request('POST','/restaurants/other/policies',body,self.tokens[0],'scoped')[0],201)
        deep='['*1100+'0'+']'*1100
        raw=(__import__('json').dumps(self.policy())[:-1]+',"ignored":'+deep+'}').encode()
        status,p=request('POST','/restaurants/r/policies',token=self.tokens[0],key='deep-policy',raw=raw);self.assertEqual(status,201)
        self.assertEqual(request('POST','/restaurants/r/policies',token=self.tokens[0],key='deep-policy',raw=raw),(200,p))
        selected=self.policy(capacities={'t0':2,'t1':2,'t2':3,'t3':8});self.publish(selected,'capacity')
        b=self.body(party=5);b.pop('table_id');b['table_ids']=['t1','t2']
        status,pair=request('POST','/reservations',b,self.tokens[0],'pair-cap');self.assertEqual(status,201)
        self.assertEqual(pair['accepted_terms']['capacities'],selected['capacities'])
        b['starts_at_local']=api.FUTURE+'T20:00';b['party_size']=6
        self.err('POST','/reservations',b,422,'party_exceeds_capacity')

    def test_series_extra_03_maximum_and_concurrent_original_receipt(self):
        anchor=self.book()
        body=dict(anchor_reference=anchor['reference'],count=12,interval_weeks=4,ignored={'number':1})
        replies=self.burst(lambda i:request('POST','/series',body,self.tokens[0],'series-max'))
        self.assertEqual(sum(s==201 for s,v in replies),1);self.assertEqual(sum(s==200 for s,v in replies),49)
        self.assertTrue(all(v==replies[0][1] for s,v in replies));original=replies[0][1]
        self.assertEqual(len(original['occurrences']),12);self.assertEqual(len(self.listing()),12)
        expected=(dt.date.fromisoformat(api.FUTURE)+dt.timedelta(days=11*4*7)).isoformat()+'T18:00'
        self.assertEqual(original['occurrences'][-1]['reservation']['starts_at_local'],expected)
        self.err('POST','/series',{},409,'idempotency_key_reuse',key='series-max')
        same=copy.deepcopy(body);same['ignored']['number']=1.0
        self.assertEqual(request('POST','/series',same,self.tokens[0],'series-max'),(200,original))
        same['ignored']['number']=True
        self.err('POST','/series',same,409,'idempotency_key_reuse',key='series-max')
        self.patch(anchor,{'party_size':3})
        self.assertEqual(request('POST','/series',body,self.tokens[0],'series-max'),(200,original))
