"""Independent policies/history/series cases authored before Stage3 source review."""
import copy
import datetime as dt
import json
import unittest
import reviewer_inherited as api

request=api.request
DAY=api.FUTURE

def policy_fixture():
    seed=api.fixture(tables=4)
    seed['restaurants'][0]['manager_user_ids']=['u0']
    seed['restaurants'][0]['combinable']=[['t2','t1'],['t1','t3']]
    return seed

class PolicyChecks(unittest.TestCase):
    reset=api.SpecChecks.reset
    login=api.SpecChecks.login
    err=api.SpecChecks.err
    listing=api.SpecChecks.listing
    burst=api.SpecChecks.burst

    def setUp(self):
        self.seed=policy_fixture();self.reset(self.seed)
        self.tokens=[self.login(i) for i in range(2)]

    def body(self,table='t1',day=DAY,clock='18:00',party=4):
        return dict(restaurant_id='r',table_id=table,starts_at_local=day+'T'+clock,party_size=party)

    def book(self,table='t1',day=DAY,clock='18:00',party=4,key='book'):
        status,row=request('POST','/reservations',self.body(table,day,clock,party),self.tokens[0],key)
        self.assertEqual(status,201);return row

    def policy(self,effective=DAY,**overrides):
        r=self.seed['restaurants'][0]
        value={k:copy.deepcopy(r[k]) for k in ['slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','opening_hours']}
        value.update(effective_from=effective,capacities={t['id']:t['capacity'] for t in r['tables']})
        value.update(overrides);return value

    def publish(self,body=None,key='policy'):
        status,value=request('POST','/restaurants/r/policies',body or self.policy(),self.tokens[0],key)
        self.assertEqual(status,201);return value

    def history(self,row,token=None):
        status,value=request('GET','/reservations/'+row['reference']+'/history',token=token or self.tokens[0])
        self.assertEqual(status,200);return value['entries']

    def patch(self,row,changes):return request('PATCH','/reservations/'+row['reference'],changes,self.tokens[0])

    def test_policy_01_explain_independent_truth_table(self):
        self.book('t0',party=1);self.book('t1',key='second')
        query='/availability?restaurant_id=r&date='+DAY+'&party_size=4'
        raw=request('GET',query)[1]
        self.assertNotIn('explain',raw)
        self.assertTrue(all('explain' not in s for s in raw['slots']))
        slots=request('GET',query+'&explain=true')[1]['slots']
        first=slots[0];byid={e['table_id']:e for e in first['explain']}
        self.assertEqual([e['table_id'] for e in first['explain']],['t0','t1','t2','t3'])
        for table,capacity,free in [('t0',False,False),('t1',True,False),('t2',True,True),('t3',True,True)]:
            entry=byid[table]
            self.assertEqual(entry,dict(table_id=table,policy_version=0,available=capacity and free,
                                       rules=[dict(rule='capacity',holds=capacity),dict(rule='no_overlap',holds=free)]))
        # A later nonoverlapping slot gives the independent capacity-false/free-true case.
        later=next(s for s in slots if s['starts_at_local'].endswith('19:30'))
        self.assertEqual(later['explain'][0]['rules'],[dict(rule='capacity',holds=False),dict(rule='no_overlap',holds=True)])
        for slot in slots:
            self.assertEqual([e['table_id'] for e in slot['explain'] if e['available']],slot['available_table_ids'])
            self.assertIn('available_options',slot)
        for v in ['false','1','','TRUE','True']:
            self.err('GET',query+'&explain='+v,None,422,'validation_failed',token=None)

    def test_policy_02_validation_authorization_version_allocation(self):
        self.assertEqual(request('GET','/restaurants/r/policies'),(200,{'policies':[]}))
        body=self.policy()
        self.err('POST','/restaurants/r/policies',body,401,'unauthenticated',token=None)
        self.err('POST','/restaurants/r/policies',body,403,'forbidden',token=self.tokens[1])
        self.err('POST','/restaurants/nope/policies',body,404,'not_found')
        invalid=[]
        for field in body:
            missing=copy.deepcopy(body);del missing[field];invalid.append(missing)
        for field,values in [('slot_minutes',[0,1441,True,1.5,'30']),('reservation_duration_minutes',[0,1441,False]),('cancellation_cutoff_minutes',[-1,10081,True]),('effective_from',['2040-02-30','2040-6-14',None])]:
            invalid.extend(dict(body,**{field:v}) for v in values)
        invalid.extend([dict(body,capacities={'t0':2}),dict(body,capacities=dict(body['capacities'],extra=4)),
                        dict(body,capacities=dict(body['capacities'],t1=True)),dict(body,capacities=dict(body['capacities'],t1=101)),
                        dict(body,opening_hours=[body['opening_hours'][0],body['opening_hours'][0]])])
        for bad in invalid:
            self.err('POST','/restaurants/r/policies',bad,422,'validation_failed',key='reusable')
        original=request('GET','/restaurants/r')[1]
        response=self.publish(body,'reusable');self.assertEqual(response['policy_version'],1)
        self.assertEqual(request('POST','/restaurants/r/policies',body,self.tokens[0],'reusable'),(200,response))
        self.err('POST','/restaurants/r/policies',{},409,'idempotency_key_reuse',key='reusable')
        self.assertEqual(request('GET','/restaurants/r')[1],original)
        self.assertEqual(request('GET','/restaurants/r/policies')[1]['policies'],[response])

    def test_policy_03_effective_date_ties_and_nonretroactivity(self):
        old=self.book();old_history=self.history(old)
        p1=self.publish(self.policy('2040-06-20',reservation_duration_minutes=60),'p1')
        p2=self.publish(self.policy('2040-06-10',reservation_duration_minutes=120),'p2')
        p3=self.publish(self.policy('2040-06-10',reservation_duration_minutes=30),'p3')
        self.assertEqual([p['policy_version'] for p in [p1,p2,p3]],[1,2,3])
        for day,version,duration in [('2040-06-09',0,90),('2040-06-10',3,30),('2040-06-19',3,30),('2040-06-20',1,60)]:
            row=self.book('t2',day=day,key=day)
            self.assertEqual(row['accepted_terms']['policy_version'],version)
            self.assertEqual((dt.datetime.fromisoformat(row['ends_at'])-dt.datetime.fromisoformat(row['starts_at'])).total_seconds(),duration*60)
            self.assertNotIn('effective_from',row['accepted_terms'])
        self.assertEqual(request('GET','/reservations/'+old['reference'],token=self.tokens[0]),(200,old))
        self.assertEqual(self.history(old),old_history)
        self.assertEqual(request('POST','/reservations',self.body(),self.tokens[0],'book'),(200,old))

    def test_policy_04_noop_real_change_terms_and_expected_revision(self):
        row=self.book();history=self.history(row)
        caps={t['id']:t['capacity'] for t in self.seed['restaurants'][0]['tables']};caps['t1']=3
        self.publish(self.policy(capacities=caps,reservation_duration_minutes=120))
        self.assertEqual(self.patch(row,{'party_size':4,'ignored':False}),(200,row))
        self.assertEqual(self.history(row),history)
        self.err('PATCH','/reservations/'+row['reference'],{'party_size':5},422,'party_exceeds_capacity')
        self.err('PATCH','/reservations/'+row['reference'],{'expected_revision':2,'party_size':False},409,'stale_revision')
        for rev in [0,-1,True,'1',1.2]:self.err('PATCH','/reservations/'+row['reference'],{'expected_revision':rev},422,'validation_failed')
        status,new=self.patch(row,{'party_size':3,'expected_revision':1});self.assertEqual(status,200)
        self.assertEqual(new['revision'],2);self.assertEqual(new['accepted_terms']['policy_version'],1)
        entries=self.history(row);self.assertEqual(entries[0],history[0])
        self.assertEqual(entries[1]['changes'],[dict(field='party_size',**{'from':4,'to':3})])
        self.assertEqual(entries[1]['accepted_terms'],new['accepted_terms'])

    def test_policy_05_history_privacy_and_cancel(self):
        row=self.book();entries=self.history(row)
        self.assertEqual(len(entries),1);self.assertEqual(entries[0]['seq'],1);self.assertEqual(entries[0]['revision'],1)
        self.assertEqual(entries[0]['event'],'created')
        self.assertEqual(entries[0]['changes'],[dict(field=k,**{'from':None,'to':v}) for k,v in [('table_id','t1'),('starts_at_local',DAY+'T18:00'),('party_size',4)]])
        for suffix in ['/history','/decision']:
            for token in [None,self.tokens[1]]:self.err('GET','/reservations/'+row['reference']+suffix,None,404,'not_found',token=token)
        status,new=self.patch(row,{'table_id':'t3','party_size':5,'starts_at_local':DAY+'T19:00'})
        self.assertEqual(status,200)
        changes=self.history(row)[1]['changes'];self.assertEqual([c['field'] for c in changes],['table_id','starts_at_local','party_size'])
        cancelled=request('POST','/reservations/'+row['reference']+'/cancel',{},self.tokens[0])[1]
        self.assertEqual(cancelled['revision'],3)
        final=self.history(row);self.assertEqual([e['seq'] for e in final],[1,2,3])
        self.assertEqual([e['at'] for e in final],sorted(e['at'] for e in final))
        self.assertEqual(final[-1]['changes'],[]);self.assertEqual(final[-1]['event'],'cancelled')
        self.assertEqual(request('POST','/reservations/'+row['reference']+'/cancel',{},self.tokens[0]),(200,cancelled))
        self.assertEqual(self.history(row),final)
        self.assertEqual(request('GET','/reservations/'+row['reference']+'/decision',token=self.tokens[0])[1],dict(reference=row['reference'],revision=3,accepted_terms=cancelled['accepted_terms']))

    def test_policy_06_pair_history_and_reversed_noop(self):
        body=self.body();del body['table_id'];body['table_ids']=['t1','t2']
        status,row=request('POST','/reservations',body,self.tokens[0],'pair');self.assertEqual(status,201)
        self.assertEqual(self.history(row)[0]['changes'][0],dict(field='table_ids',**{'from':None,'to':['t2','t1']}))
        self.assertEqual(self.patch(row,{'table_ids':['t1','t2']}),(200,row))
        status,single=self.patch(row,{'table_id':'t3'});self.assertEqual(status,200)
        self.assertEqual(self.history(row)[1]['changes'],[dict(field='table_ids',**{'from':['t2','t1'],'to':['t3']})])
        status,again=self.patch(row,{'table_ids':['t1','t2']});self.assertEqual(status,200)
        self.assertEqual(self.history(row)[2]['changes'],[dict(field='table_ids',**{'from':['t3'],'to':['t2','t1']})])

    def test_policy_07_concurrent_publication_and_cas(self):
        body=self.policy()
        replies=self.burst(lambda i:request('POST','/restaurants/r/policies',body,self.tokens[0],'same-policy'))
        self.assertEqual(sum(s==201 for s,v in replies),1);self.assertEqual(sum(s==200 for s,v in replies),49)
        self.assertTrue(all(v==replies[0][1] for s,v in replies))
        row=self.book()
        replies=self.burst(lambda i:self.patch(row,{'party_size':3,'expected_revision':1}))
        self.assertEqual(sum(s==200 for s,v in replies),1)
        self.assertEqual(sum(s==409 and v['error']['code']=='stale_revision' for s,v in replies),49)
        self.assertEqual(len(self.history(row)),2)

    def adopt(self,row,count=3,interval=1,key='adopt'):
        body=dict(anchor_reference=row['reference'],count=count,interval_weeks=interval)
        status,value=request('POST','/series',body,self.tokens[0],key)
        self.assertEqual(status,201);return body,value

    def series(self,value,token='default'):
        return request('GET','/series/'+value['series_id'],token=self.tokens[0] if token=='default' else token)

    def test_series_01_anchor_identity_dates_and_original_receipt(self):
        anchor=self.book();history=self.history(anchor)
        body,series=self.adopt(anchor,count=4,interval=2)
        self.assertEqual(series['revision'],1);self.assertEqual(series['interval_weeks'],2)
        self.assertEqual(series['occurrences'][0]['reservation'],anchor)
        self.assertEqual(self.history(anchor),history)
        self.assertEqual(request('POST','/reservations',self.body(),self.tokens[0],'book'),(200,anchor))
        self.assertEqual([o['index'] for o in series['occurrences']],[0,1,2,3])
        self.assertEqual(len(set(o['reference'] for o in series['occurrences'])),4)
        for i,o in enumerate(series['occurrences']):
            expected=(dt.date.fromisoformat(DAY)+dt.timedelta(days=14*i)).isoformat()+'T18:00'
            self.assertEqual(o['reservation']['starts_at_local'],expected);self.assertFalse(o['exception'])
        self.assertEqual(self.series(series),(200,series))
        for token in [None,self.tokens[1]]:self.assertEqual(self.series(series,token)[0],404)
        self.assertEqual(request('POST','/series',body,self.tokens[0],'adopt'),(200,series))
        self.err('POST','/series',body,409,'already_in_series',key='again')

    def test_series_02_validation_rollback_and_failed_key_reuse(self):
        anchor=self.book();body=dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1)
        for field,values in [('count',[1,13,True,'3',2.5]),('interval_weeks',[0,5,False,'1'])]:
            for value in values:self.err('POST','/series',dict(body,**{field:value}),422,'validation_failed')
        self.err('POST','/series',body,401,'unauthenticated',token=None)
        self.err('POST','/series',body,404,'not_found',token=self.tokens[1])
        nextday=(dt.date.fromisoformat(DAY)+dt.timedelta(days=7)).isoformat()
        blocker=self.book(day=nextday,key='blocker')
        before=self.listing();hist=self.history(anchor)
        self.err('POST','/series',body,409,'table_unavailable',key='reusable')
        self.assertEqual(self.listing(),before);self.assertEqual(self.history(anchor),hist)
        request('POST','/reservations/'+blocker['reference']+'/cancel',{},self.tokens[0])
        status,series=request('POST','/series',body,self.tokens[0],'reusable');self.assertEqual(status,201)
        self.assertEqual(len(series['occurrences']),3)

    def test_series_03_exception_cancel_noop_and_batch_revision(self):
        anchor=self.book();body,series=self.adopt(anchor,count=4)
        occurrences=series['occurrences']
        r1=occurrences[1]['reservation'];r2=occurrences[2]['reservation']
        self.assertEqual(self.patch(r1,{'party_size':4})[0],200)
        self.assertEqual(self.series(series)[1],series)
        moves={'moves':[{'reference':r1['reference'],'party_size':3},{'reference':r2['reference'],'party_size':2}]}
        status,_=request('POST','/reservation-moves',moves,self.tokens[0],'series-batch');self.assertEqual(status,201)
        current=self.series(series)[1];self.assertEqual(current['revision'],2)
        self.assertEqual([o['exception'] for o in current['occurrences']],[False,True,True,False])
        request('POST','/reservations/'+anchor['reference']+'/cancel',{},self.tokens[0])
        cancelled=self.series(series)[1];self.assertEqual(cancelled['revision'],3)
        self.assertFalse(cancelled['occurrences'][0]['exception'])
        self.assertEqual([o['reservation']['status'] for o in cancelled['occurrences']],['cancelled','confirmed','confirmed','confirmed'])
        request('POST','/reservations/'+anchor['reference']+'/cancel',{},self.tokens[0])
        self.assertEqual(self.series(series)[1],cancelled)
        self.assertEqual(request('POST','/series',body,self.tokens[0],'adopt'),(200,series))

    def test_series_04_future_dst_gap_and_policy_per_occurrence(self):
        seed=policy_fixture();seed['restaurants'][0].update(timezone='Europe/Berlin',opening_hours=[dict(weekday='sun',opens='00:00',closes='06:00')])
        self.reset(seed);self.seed=seed;self.tokens=[self.login(i) for i in range(2)]
        anchor=self.book(day='2030-03-24',clock='02:30')
        body=dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1)
        self.err('POST','/series',body,422,'invalid_local_time',key='gap')
        self.assertEqual(self.listing(),[anchor])
        fall=self.book(day='2030-10-20',clock='02:30',key='fall')
        self.publish(self.policy('2030-10-27',reservation_duration_minutes=120))
        _,series=self.adopt(fall,count=2,key='fall-series')
        generated=series['occurrences'][1]['reservation']
        self.assertTrue(generated['starts_at'].endswith('+02:00'))
        self.assertEqual(generated['accepted_terms']['policy_version'],1)
        self.assertEqual((dt.datetime.fromisoformat(generated['ends_at'])-dt.datetime.fromisoformat(generated['starts_at'])).total_seconds(),7200)
