"""Independent Stage4 preview/apply contracts and exhaustive objective comparison."""
import copy
import random
import unittest
import reviewer_inherited as api
from reviewer_policy_checks import PolicyChecks,policy_fixture
from reviewer_closure_oracle import solve

request=api.request

def closure_fixture():
    seed=policy_fixture();r=seed['restaurants'][0]
    r['tables']=[dict(id='t'+str(i),label='Seating '+str(i),capacity=c) for i,c in enumerate([2,3,4,5,6,8])]
    r['combinable']=[['t1','t0'],['t2','t1'],['t3','t2'],['t5','t4']]
    seed['restaurants'][1]['manager_user_ids']=['u0']
    return seed

class ReplanChecks(unittest.TestCase):
    reset=PolicyChecks.reset;login=PolicyChecks.login;err=PolicyChecks.err;listing=PolicyChecks.listing
    body=PolicyChecks.body;book=PolicyChecks.book;policy=PolicyChecks.policy;publish=PolicyChecks.publish
    history=PolicyChecks.history;patch=PolicyChecks.patch;adopt=PolicyChecks.adopt;series=PolicyChecks.series;burst=PolicyChecks.burst

    def setUp(self):
        self.seed=closure_fixture();self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)];self.counter=0

    def closure(self,table='t0',start='18:00',end='19:00',day=api.FUTURE):
        return {'table_id':table,'from':day+'T'+start+':00+00:00','to':day+'T'+end+':00+00:00'}

    def preview(self,closure=None,key=None,rid='r'):
        self.counter+=1
        return request('POST','/restaurants/'+rid+'/replans',closure or self.closure(),self.tokens[0],key or 'preview'+str(self.counter))

    def apply(self,plan,key='apply',rid='r'):
        return request('POST','/restaurants/'+rid+'/replans/'+plan['plan_id']+'/apply',{},self.tokens[0],key)

    def revision(self):
        status,p=self.preview(self.closure(day='2099-01-01'));self.assertEqual(status,201);return p['restaurant_revision']

    def assert_oracle(self,records,closure,existing=()):
        expected=solve(self.seed['restaurants'][0],records,closure,existing)
        before=self.listing();hist={r['reference']:self.history(r) for r in before}
        status,plan=self.preview(closure)
        if expected is None:
            self.assertEqual((status,plan['error']['code']),(409,'no_feasible_plan'))
        else:
            self.assertEqual(status,201)
            for k in ['assignments','moved_count','unused_seats']:self.assertEqual(plan[k],expected[k],k)
        self.assertEqual(self.listing(),before)
        for r in before:self.assertEqual(self.history(r),hist[r['reference']])
        return expected,plan

    def test_replan_01_manager_interval_and_failed_state(self):
        before=request('GET','/_test/export')[1]
        body=self.closure();path='/restaurants/r/replans'
        self.err('POST',path,body,401,'unauthenticated',token=None)
        self.err('POST',path,body,403,'forbidden',token=self.tokens[1])
        self.err('POST','/restaurants/unknown/replans',body,404,'not_found')
        self.err('POST',path,dict(body,table_id='unknown'),404,'not_found')
        for invalid in [dict(body,**{'from':'2040-06-14T18:00'}),dict(body,to=body['from']),dict(body,**{'from':body['to'],'to':body['from']}),dict(body,to=False),dict(body,**{'from':'nonsense'})]:
            self.err('POST',path,invalid,422,'validation_failed',key='reusable')
        self.assertTrue(request('GET','/_test/export')[1]==before,'Rejected preview changed private state')
        status,plan=self.preview(body,key='reusable');self.assertEqual(status,201);self.assertEqual(plan['restaurant_revision'],0)
        self.assertEqual(plan['assignments'],[])
        self.assertEqual(request('POST',path,body,self.tokens[0],'reusable'),(200,plan))
        self.err('POST',path,{},409,'idempotency_key_reuse',key='reusable')

    def test_replan_02_exhaustive_objective_fixed_and_accepted_capacities(self):
        rng=random.Random(72641)
        for case in range(12):
            with self.subTest(case=case):
                self.seed=closure_fixture();self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
                records=[]
                for i,t in enumerate(['t0','t2','t4']):
                    cap=self.seed['restaurants'][0]['tables'][int(t[1:])]['capacity']
                    records.append(self.book(t,party=rng.randint(1,cap),key='book'+str(i)))
                    if i==0 and case%3==0:
                        caps={t['id']:t['capacity']+1 for t in self.seed['restaurants'][0]['tables']}
                        self.publish(self.policy(capacities=caps),'larger-policy')
                records.append(self.book('t1',clock='19:00',party=2,key='fixed'))
                closure=self.closure(table='t'+str(case%6),end='18:30')
                self.assert_oracle(records,closure)

    def test_replan_03_six_considered_and_declared_pairs(self):
        self.seed['restaurants'][0]['reservation_duration_minutes']=30
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        records=[self.book('t0',clock=c,party=2,key=c) for c in ['18:00','18:30','19:00','19:30','20:00','20:30']]
        expected,plan=self.assert_oracle(records,self.closure(end='21:00'))
        self.assertIsNotNone(expected);self.assertEqual(len(plan['assignments']),6)
        self.assertEqual(plan['moved_count'],6)
        # Larger party requires a declared pair under accepted capacities.
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        body=self.body('t0',party=12);body.pop('table_id');body['table_ids']=['t5','t4']
        status,row=request('POST','/reservations',body,self.tokens[0],'pair');self.assertEqual(status,201)
        expected,plan=self.assert_oracle([row],self.closure('t4'))
        self.assertIsNone(expected)

    def test_replan_04_apply_history_terms_and_closure_occupancy(self):
        moved=self.book('t0',party=2);stable=self.book('t5',party=7,key='stable')
        histories={r['reference']:self.history(r) for r in [moved,stable]}
        body=self.closure();expected,plan=self.assert_oracle([moved,stable],body)
        self.assertEqual(plan['restaurant_revision'],2)
        status,result=self.apply(plan);self.assertEqual(status,201);self.assertEqual(result['restaurant_revision'],3)
        assignments={a['reference']:a for a in plan['assignments']}
        self.assertEqual([r['reference'] for r in result['reservations']],sorted(assignments))
        for row in result['reservations']:
            original=next(r for r in [moved,stable] if r['reference']==row['reference'])
            a=assignments[row['reference']]
            for field in ['reference','reservation_id','party_size','starts_at','starts_at_local','ends_at','accepted_terms','created_at']:
                self.assertEqual(row[field],original[field])
            self.assertEqual(row['table_ids'],a['table_ids'])
            self.assertEqual(row['revision'],original['revision']+int(a['changed']))
            hist=self.history(row)
            self.assertEqual(hist[:len(histories[row['reference']])],histories[row['reference']])
            if a['changed']:
                self.assertEqual(hist[-1]['event'],'reassigned');self.assertEqual(hist[-1]['plan_id'],plan['plan_id'])
                self.assertEqual(hist[-1]['changes'],[dict(field='table_ids',**{'from':original['table_ids'],'to':a['table_ids']})])
            else:self.assertEqual(hist,histories[row['reference']])
        slots=request('GET','/availability?restaurant_id=r&date='+api.FUTURE+'&party_size=1&explain=true')[1]['slots']
        first=slots[0];self.assertNotIn('t0',first['available_table_ids'])
        self.assertTrue(all('t0' not in o['table_ids'] for o in first['available_options']))
        self.assertFalse(first['explain'][0]['rules'][1]['holds'])
        self.err('POST','/reservations',self.body('t0',party=1),409,'table_unavailable')
        self.assertEqual(self.apply(plan),(200,result))
        self.err('POST','/restaurants/r/replans/'+plan['plan_id']+'/apply',{},409,'plan_already_applied',key='new-apply')

    def test_replan_05_stale_and_cross_restaurant_revision(self):
        self.book('t0',party=2);status,plan=self.preview();self.assertEqual(status,201)
        other=dict(self.body('other_table'),restaurant_id='other')
        self.assertEqual(request('POST','/reservations',other,self.tokens[0],'other')[0],201)
        self.assertEqual(self.apply(plan)[0],201)
        status,stale=self.preview(self.closure('t1'));self.assertEqual(status,201)
        self.book('t4',clock='20:00',party=2,key='invalidate')
        before=self.listing();self.assertEqual(self.apply(stale,'stale')[0],409)
        self.err('POST','/restaurants/r/replans/'+stale['plan_id']+'/apply',{},409,'stale_plan',key='stale')
        self.assertEqual(self.listing(),before)
        self.err('POST','/restaurants/other/replans/'+stale['plan_id']+'/apply',{},404,'not_found')

    def test_replan_06_revision_once_per_real_operation(self):
        self.assertEqual(self.revision(),0)
        row=self.book('t0',party=2);self.assertEqual(self.revision(),1)
        self.patch(row,{'party_size':2});self.assertEqual(self.revision(),1)
        self.patch(row,{'party_size':1});self.assertEqual(self.revision(),2)
        request('POST','/reservations/'+row['reference']+'/cancel',{},self.tokens[0]);self.assertEqual(self.revision(),3)
        request('POST','/reservations/'+row['reference']+'/cancel',{},self.tokens[0]);self.assertEqual(self.revision(),3)
        self.publish();self.assertEqual(self.revision(),4)
        status,empty=self.preview(self.closure(day='2098-01-01'));self.assertEqual(status,201)
        self.assertEqual(self.apply(empty)[0],201);self.assertEqual(self.revision(),5)
        self.assertEqual(self.apply(empty)[0],200);self.assertEqual(self.revision(),5)

    def test_replan_07_concurrent_apply_and_atomic_export(self):
        self.book('t0',party=2);status,plan=self.preview();self.assertEqual(status,201)
        replies=self.burst(lambda i:self.apply(plan,'same-apply'))
        self.assertEqual(sum(s==201 for s,v in replies),1);self.assertEqual(sum(s==200 for s,v in replies),49)
        self.assertTrue(all(v==replies[0][1] for s,v in replies));self.assertEqual(self.revision(),2)
        self.assertEqual(len(self.history(replies[0][1]['reservations'][0])),2)

    def test_replan_08_past_cutoff_operator_and_prior_closure(self):
        old=self.book('t0',day='2000-06-14',party=2)
        c=self.closure(day='2000-06-14');status,plan=self.preview(c);self.assertEqual(status,201)
        self.assertEqual(self.apply(plan)[0],201)
        current=self.listing()
        new=self.closure('t1',day='2000-06-14')
        expected,plan2=self.assert_oracle(current,new,[c]);self.assertIsNotNone(expected)
        self.assertTrue(all('t0' not in a['table_ids'] and 't1' not in a['table_ids'] for a in plan2['assignments']))
        self.assertEqual(self.apply(plan2,'apply2')[0],201)

    def test_replan_09_competing_applications_and_atomic_reads(self):
        self.seed['restaurants'][0]['reservation_duration_minutes']=30
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        rows=[self.book('t0',clock=c,party=2,key=c) for c in ['18:00','18:30','19:00','19:30','20:00','20:30']]
        _,plan=self.preview(self.closure(end='21:00'));before=self.listing()
        replies=self.burst(lambda i: self.apply(plan,'apply-'+str(i)) if i%2==0 else request('GET','/reservations',token=self.tokens[0]))
        writes=replies[::2];reads=[v['reservations'] for s,v in replies[1::2]]
        self.assertEqual(sum(s==201 for s,v in writes),1)
        self.assertTrue(all(s==201 or (s==409 and v['error']['code']=='plan_already_applied') for s,v in writes))
        after=self.listing();self.assertNotEqual(before,after)
        self.assertTrue(all(value==before or value==after for value in reads))
        self.assertEqual(self.revision(),7)
        for row in after:self.assertEqual(row['revision'],2);self.assertEqual(len(self.history(row)),2)

    def test_replan_10_half_open_closure_failed_key_and_original_apply_receipt(self):
        self.seed['restaurants'][0]['reservation_duration_minutes']=30
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        self.book('t0',clock='18:00',party=2,key='before')
        self.book('t0',clock='19:00',party=2,key='after')
        c=self.closure(start='18:30',end='19:00');_,plan=self.preview(c)
        self.assertEqual(plan['assignments'],[])
        status,receipt=self.apply(plan);self.assertEqual(status,201)
        self.err('POST','/reservations',self.body('t0',clock='18:30',party=2),409,'table_unavailable',key='closed')
        self.assertEqual(request('POST','/reservations',self.body('t0',clock='19:30',party=2),self.tokens[0],'closed')[0],201)
        self.assertEqual(self.apply(plan),(200,receipt))
        # Saturation forces a genuine failed preview, which cannot claim its key.
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        for i in range(6):self.book('t'+str(i),party=1,key='full'+str(i))
        snapshot=request('GET','/_test/export')[1]
        self.err('POST','/restaurants/r/replans',self.closure(),409,'no_feasible_plan',key='retry-plan')
        self.assertTrue(request('GET','/_test/export')[1]==snapshot,'Failed preview changed private state')
        status,new=self.preview(self.closure(day='2040-06-15'),key='retry-plan');self.assertEqual(status,201)
        self.assertEqual(new['assignments'],[])
