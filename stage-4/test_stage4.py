"""Closure planning and series amendments, with an independent exhaustive oracle."""
import copy
import itertools
import os
import random
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import test_contract as base
import test_stage3 as prior


def oracle(r, bookings, closing):
    options = [[t['id']] for t in r['tables']] + r.get('combinable', [])
    candidates = sorted(bookings,key=lambda b:b['reference'])
    best, answer = None, None
    for ranks in itertools.product(range(len(options)), repeat=len(candidates)):
        assignments = [options[rank] for rank in ranks]
        if any(closing in ids for ids in assignments):
            continue
        if any(set(ids) & set(other) for i,ids in enumerate(assignments) for other in assignments[i+1:]):
            continue
        waste = [sum(b['accepted_terms']['capacities'][t] for t in ids)-b['party_size'] for b,ids in zip(candidates,assignments)]
        if any(n < 0 for n in waste):
            continue
        moved = [set(b['table_ids']) != set(ids) for b,ids in zip(candidates,assignments)]
        score = (sum(moved),sum(waste),ranks)
        if best is None or score < best:
            best=score
            answer=[{'reference':b['reference'],'table_ids':ids,'changed':change} for b,ids,change in zip(candidates,assignments,moved)]
    return None if best is None else {'assignments':answer,'moved_count':best[0],'unused_seats':best[1]}


class Stage4(unittest.TestCase):
    setUpClass=classmethod(base.Contract.setUpClass.__func__)
    tearDownClass=classmethod(base.Contract.tearDownClass.__func__)
    request=base.Contract.request
    login=base.Contract.login
    booking=base.Contract.booking
    create=base.Contract.create
    error=base.Contract.error
    snapshot=base.Contract.snapshot
    setUp=prior.Stage3.setUp
    policy=prior.Stage3.policy
    publish=prior.Stage3.publish
    history=prior.Stage3.history
    adopt=prior.Stage3.adopt

    def closure(self,**changes):
        return {'table_id':'t1','from':'2032-10-25T19:00:00+02:00','to':'2032-10-25T20:30:00+02:00',**changes}

    def preview(self,key='preview',**changes):
        status,plan=self.request('POST','/restaurants/r/replans',self.closure(**changes),self.bob,key)
        self.assertEqual(status,201)
        return plan

    def apply(self,plan,key='apply',server=0):
        return self.request('POST','/restaurants/r/replans/'+plan['plan_id']+'/apply',{},self.bob,key,server=server)

    def test_solver_matches_independent_exhaustive_objective(self):
        rng=random.Random(817)
        for case in range(18):
            seed=prior.fixture()
            seed['reservations']=[{**self.booking(table_id='t'+str(n+1),party_size=rng.randint(1,(n+1)*2)),
                                    'id':'seed'+str(n),'reference':'BOOK00'+str(3-n),'user_id':'ada'} for n in range(3)]
            self.assertEqual(self.request('POST','/_test/reset',seed)[0],204)
            self.ada,self.bob=self.login('ada'),self.login('bob')
            bookings=self.request('GET','/reservations',token=self.ada)[1]['reservations']
            closing='t'+str(1+case%4)
            expected=oracle(seed['restaurants'][0],bookings,closing)
            status,plan=self.request('POST','/restaurants/r/replans',self.closure(table_id=closing),self.bob,'oracle')
            if expected is None:
                self.error((status,plan),409,'no_feasible_plan')
            else:
                self.assertEqual(status,201)
                self.assertEqual({k:plan[k] for k in expected},expected)

    def test_preview_is_read_only_apply_past_cutoff_and_history(self):
        a=self.create(starts_at_local='2020-10-25T19:00')
        before=self.snapshot()['state']
        plan=self.preview(**{'from':'2020-10-25T19:00:00+01:00','to':'2020-10-25T20:30:00+01:00'})
        after=self.snapshot()['state']
        self.assertTrue(all(before[k]==after[k] for k in before if k not in ('plans','receipts')))
        status,response=self.apply(plan)
        self.assertEqual(status,201)
        moved=response['reservations'][0]
        for key in ('reference','reservation_id','created_at','starts_at','ends_at','party_size','accepted_terms'):
            self.assertEqual(moved[key],a[key])
        self.assertEqual(moved['revision'],2)
        entry=self.history(a['reference'])[-1]
        self.assertEqual(entry['event'],'reassigned')
        self.assertEqual(entry['plan_id'],plan['plan_id'])
        self.assertEqual(entry['changes'],[{'field':'table_ids','from':['t1'],'to':moved['table_ids']}])
        self.assertEqual(self.apply(plan),(200,response))
        self.error(self.apply(plan,'other'),409,'plan_already_applied')

    def test_closure_half_open_options_and_failed_key_reuse(self):
        plan=self.preview(); self.assertEqual(self.apply(plan)[0],201)
        for body in [self.booking(),{**{k:v for k,v in self.booking().items() if k!='table_id'},'table_ids':['t1','t2']}]:
            self.error(self.request('POST','/reservations',body,self.ada,'blocked'),409,'table_unavailable')
        self.create('blocked',starts_at_local='2032-10-25T20:30')
        data=self.request('GET','/availability?restaurant_id=r&date=2032-10-25&party_size=2&explain=true')[1]
        at19=next(s for s in data['slots'] if s['starts_at_local'].endswith('19:00'))
        self.assertNotIn('t1',at19['available_table_ids'])
        self.assertFalse(at19['explain'][0]['rules'][1]['holds'])
        self.assertFalse(any('t1' in o['table_ids'] for o in at19['available_options']))

    def test_apply_50_identical_stale_and_cross_restaurant_isolation(self):
        seed=prior.fixture(); second=copy.deepcopy(seed['restaurants'][0]); second['id']='other'; seed['restaurants'].append(second)
        self.request('POST','/_test/reset',seed); self.ada,self.bob=self.login('ada'),self.login('bob')
        a=self.create(); plan=self.preview()
        self.create('other',restaurant_id='other')
        self.request('PATCH','/reservations/'+a['reference'],{'party_size':2},self.ada)
        with ThreadPoolExecutor(max_workers=50) as pool:
            results=list(pool.map(lambda _:self.apply(plan),range(50)))
        self.assertEqual(sum(status==201 for status,_ in results),1)
        self.assertEqual(sum(status==200 for status,_ in results),49)
        self.assertTrue(all(result[1]==results[0][1] for result in results))
        stale=self.preview('stale',table_id='t4')
        self.publish()
        before=self.snapshot()
        self.error(self.apply(stale,'stale'),409,'stale_plan')
        self.assertTrue(before==self.snapshot())

    def test_validation_limits_permissions_and_no_feasible_rollback(self):
        self.error(self.request('POST','/restaurants/r/replans',self.closure(),key='x'),401,'unauthenticated')
        self.error(self.request('POST','/restaurants/r/replans',self.closure(),self.ada,'x'),403,'forbidden')
        for change in [{'from':'2032-10-25T19:00:00'},{'to':True},{'to':'2032-10-25T18:00:00+01:00'}]:
            self.error(self.request('POST','/restaurants/r/replans',self.closure(**change),self.bob,'x'),422,'validation_failed')
        seed=prior.fixture(); seed['restaurants'][0]['tables']=[{'id':'t1','label':'Only table','capacity':2}]; seed['restaurants'][0]['combinable']=[]
        self.request('POST','/_test/reset',seed); self.ada,self.bob=self.login('ada'),self.login('bob')
        self.create(); before=self.snapshot()
        self.error(self.request('POST','/restaurants/r/replans',self.closure(),self.bob,'x'),409,'no_feasible_plan')
        self.assertTrue(before==self.snapshot())
        seed=prior.fixture(); seed['restaurants'][0]['tables'] += [{'id':'t'+str(i),'label':str(i),'capacity':2} for i in range(5,8)]
        self.request('POST','/_test/reset',seed); self.bob=self.login('bob')
        self.error(self.request('POST','/restaurants/r/replans',self.closure(),self.bob,'x'),422,'planning_limit')

    def test_series_amend_exceptions_cancelled_noop_and_50_revision_race(self):
        a=self.create(); series=self.adopt(a,count=4)
        refs=[o['reference'] for o in series['occurrences']]
        self.request('PATCH','/reservations/'+refs[1],{'starts_at_local':'2032-11-02T19:00'},self.ada)
        self.request('POST','/reservations/'+refs[2]+'/cancel',{},self.ada)
        path='/series/'+series['series_id']+'/amend'
        body={'expected_revision':3,'from_index':0,'local_time':'20:00'}
        with ThreadPoolExecutor(max_workers=50) as pool:
            results=list(pool.map(lambda n:self.request('POST',path,body,self.ada,'amend'+str(n)),range(50)))
        self.assertEqual(sum(status==201 for status,_ in results),1)
        self.assertEqual(sum(status==409 and result['error']['code']=='stale_revision' for status,result in results),49)
        current=next(result for status,result in results if status==201)
        self.assertEqual(current['revision'],4)
        self.assertEqual([o['exception'] for o in current['occurrences']],[False,True,False,False])
        self.assertEqual([o['reservation']['starts_at_local'] for o in current['occurrences']],
                         ['2032-10-25T20:00','2032-11-02T19:00','2032-11-08T19:00','2032-11-15T20:00'])
        before=self.snapshot()['state']['restaurant_revisions']['r']
        self.assertEqual(self.request('POST',path,{**body,'expected_revision':4},self.ada,'noop'),(201,current))
        self.assertEqual(self.snapshot()['state']['restaurant_revisions']['r'],before)
        self.assertEqual(self.request('POST','/_test/import',self.snapshot(),server=1)[0],204)

    def test_series_amend_rollback_and_operator_move_preserves_schedule(self):
        a=self.create(); series=self.adopt(a)
        plan=self.preview(); self.assertEqual(self.apply(plan)[0],201)
        current=self.request('GET','/series/'+series['series_id'],token=self.ada)[1]
        self.assertEqual(current['revision'],2)
        self.assertFalse(current['occurrences'][0]['exception'])
        body={'expected_revision':2,'from_index':0,'local_time':'21:00'}
        path='/series/'+series['series_id']+'/amend'
        self.create('obstacle',starts_at_local='2032-11-01T21:00')
        before=self.snapshot()
        self.error(self.request('POST',path,body,self.ada,'amend'),409,'table_unavailable')
        self.assertTrue(before==self.snapshot())
        response=self.request('POST',path,{**body,'local_time':'18:00'},self.ada,'amend')
        self.assertEqual(response[0],201)
        self.assertEqual(response[1]['revision'],3)
        self.assertEqual([o['reservation']['starts_at_local'][:10] for o in response[1]['occurrences']],['2032-10-25','2032-11-01','2032-11-08'])
        self.assertEqual(response[1]['occurrences'][0]['reservation']['table_ids'],current['occurrences'][0]['reservation']['table_ids'])
        self.assertEqual(self.request('POST',path,{**body,'local_time':'18:00'},self.ada,'amend'),(200,response[1]))

    def test_portable_plans_applied_history_and_original_receipts(self):
        a=self.create(); plan=self.preview()
        snapshot=self.snapshot()
        self.assertEqual(self.request('POST','/_test/import',snapshot,server=1)[0],204)
        status,applied=self.apply(plan,server=1)
        self.assertEqual(status,201)
        exported=self.snapshot(server=1)
        self.assertEqual(self.request('POST','/_test/import',exported)[0],204)
        self.assertTrue(exported==self.snapshot())
        self.assertEqual(self.apply(plan),(200,applied))
        self.assertEqual(self.request('POST','/reservations',self.booking(),self.ada,'new'),(200,a))
        bad=copy.deepcopy(exported); bad['state']['plans'][0]['assignments'][0]['table_ids']=['t1']
        self.error(self.request('POST','/_test/import',bad),422,'validation_failed')
        self.assertTrue(exported==self.snapshot())

    def test_real_stage3_series_upgrade_then_repair_and_collective_amend(self):
        self.urls.append(os.environ['TABLEKEEPER_STAGE3_URL']); index=len(self.urls)-1
        self.request('POST','/_test/reset',prior.fixture(),server=index)
        token=self.login('ada',server=index); manager=self.login('bob',server=index)
        original=self.request('POST','/reservations',self.booking(),token,'anchor',server=index)[1]
        series=self.request('POST','/series',{'anchor_reference':original['reference'],'count':4,'interval_weeks':1},token,'series',server=index)[1]
        refs=[o['reference'] for o in series['occurrences']]
        self.request('PATCH','/reservations/'+refs[1],{'party_size':1},token,server=index)
        self.request('POST','/reservations/'+refs[2]+'/cancel',{},token,server=index)
        self.assertEqual(self.request('POST','/_test/import',self.snapshot(server=index))[0],204)
        self.ada,self.bob=token,manager
        plan=self.preview(); self.assertEqual(self.apply(plan)[0],201)
        result=self.request('POST','/series/'+series['series_id']+'/amend',{'expected_revision':4,'from_index':0,'local_time':'21:00'},token,'amend')
        self.assertEqual(result[0],201)
        self.assertEqual(result[1]['revision'],5)
        self.assertEqual(self.request('POST','/series',{'anchor_reference':original['reference'],'count':4,'interval_weeks':1},token,'series'),(200,series))
        self.assertEqual(self.request('POST','/_test/import',self.snapshot(),server=1)[0],204)

    def test_pair_reassignment_accepted_capacity_and_snapshot_after_later_edit(self):
        seed=prior.fixture(); seed['restaurants'][0]['tables'][2]['capacity']=4
        self.request('POST','/_test/reset',seed); self.ada,self.bob=self.login('ada'),self.login('bob')
        original=self.create(table_id='t4',party_size=6)
        # Later capacities must not affect an already accepted booking's repair.
        self.publish(capacities={'t1':1,'t2':1,'t3':1,'t4':8})
        plan=self.preview(table_id='t4')
        self.assertEqual(plan['assignments'][0]['table_ids'],['t2','t1'])
        moved=self.apply(plan)[1]['reservations'][0]
        self.assertNotIn('table_id',moved)
        self.assertEqual(moved['accepted_terms'],original['accepted_terms'])
        self.assertEqual(self.request('POST','/_test/import',self.snapshot(),server=1)[0],204)
        self.request('POST','/reservations/'+original['reference']+'/cancel',{},self.ada)
        self.assertEqual(self.request('POST','/_test/import',self.snapshot(),server=1)[0],204)

    def test_full_intervals_respect_fixed_bookings_and_earlier_closures(self):
        earlier=self.preview(table_id='t3',**{'from':'2032-10-25T20:00:00+02:00','to':'2032-10-25T20:30:00+02:00'})
        self.assertEqual(self.apply(earlier)[0],201)
        a=self.create()
        fixed=self.create('fixed',table_id='t2',starts_at_local='2032-10-25T20:00')
        plan=self.preview('second',**{'to':'2032-10-25T19:30:00+02:00'})
        self.assertEqual(plan['assignments'],[{'reference':a['reference'],'table_ids':['t4'],'changed':True}])
        self.assertEqual(self.apply(plan,'second')[0],201)
        self.assertEqual(self.request('GET','/reservations/'+fixed['reference'],token=self.ada)[1],fixed)
        self.assertEqual(self.request('POST','/_test/import',self.snapshot(),server=1)[0],204)

    def test_full_supported_planning_dimensions(self):
        seed=prior.fixture(); r=seed['restaurants'][0]; r['reservation_duration_minutes']=30
        r['tables'] += [{'id':'t5','label':'5','capacity':2},{'id':'t6','label':'6','capacity':2}]
        r['combinable']=[['t1','t2'],['t2','t3'],['t3','t4'],['t5','t6']]
        seed['reservations']=[{**self.booking(starts_at_local='2032-10-25T'+time),
                                'id':'seed'+str(n),'reference':'BOOK00'+str(n),'user_id':'ada'}
                               for n,time in enumerate(['18:00','18:30','19:00','19:30','20:00','20:30'])]
        self.assertEqual(self.request('POST','/_test/reset',seed)[0],204)
        self.ada,self.bob=self.login('ada'),self.login('bob')
        plan=self.preview(**{'from':'2032-10-25T18:00:00+02:00','to':'2032-10-25T21:00:00+02:00'})
        self.assertEqual(plan['moved_count'],6); self.assertEqual(plan['unused_seats'],0)
        self.assertEqual([a['table_ids'] for a in plan['assignments']],[['t5']]*6)
        self.assertEqual(self.apply(plan)[0],201)


if __name__ == '__main__': unittest.main(verbosity=2)
