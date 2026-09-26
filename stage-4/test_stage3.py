"""Specification-derived policy/history/recurrence and real upgrade checks."""
import copy
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_contract as base
from test_stage2 import fixture as pair_fixture


def fixture():
    seed = pair_fixture()
    seed['restaurants'][0]['manager_user_ids'] = ['bob']
    return seed


class Stage3(unittest.TestCase):
    setUpClass = classmethod(base.Contract.setUpClass.__func__)
    tearDownClass = classmethod(base.Contract.tearDownClass.__func__)
    request = base.Contract.request
    login = base.Contract.login
    booking = base.Contract.booking
    create = base.Contract.create
    error = base.Contract.error
    snapshot = base.Contract.snapshot

    def setUp(self):
        self.assertEqual(self.request('POST', '/_test/reset', fixture())[0], 204)
        self.ada, self.bob = self.login('ada'), self.login('bob')

    def policy(self, **changes):
        r = fixture()['restaurants'][0]
        return {'effective_from':'2032-10-25', 'slot_minutes':30, 'reservation_duration_minutes':120,
                'cancellation_cutoff_minutes':60, 'opening_hours':r['opening_hours'],
                'capacities':{t['id']: t['capacity'] for t in r['tables']}, **changes}

    def publish(self, key='policy', **changes):
        result = self.request('POST','/restaurants/r/policies',self.policy(**changes),self.bob,key)
        self.assertEqual(result[0],201)
        return result[1]

    def history(self, reference):
        return self.request('GET','/reservations/'+reference+'/history',token=self.ada)[1]['entries']

    def adopt(self, anchor, key='series', **changes):
        result = self.request('POST','/series',{'anchor_reference':anchor['reference'],'count':3,'interval_weeks':1,**changes},self.ada,key)
        self.assertEqual(result[0],201)
        return result[1]

    def test_policy_selection_immutable_terms_and_noops(self):
        original = self.create()
        first = self.publish(effective_from='2032-11-01')
        second = self.publish('earlier',effective_from='2032-10-01',reservation_duration_minutes=60)
        third = self.publish('tie',effective_from='2032-11-01',reservation_duration_minutes=150)
        self.assertEqual([first['policy_version'],second['policy_version'],third['policy_version']],[1,2,3])
        self.assertEqual(self.request('GET','/restaurants/r/policies')[1]['policies'],[first,second,third])
        self.assertEqual(self.request('GET','/restaurants/r')[1]['reservation_duration_minutes'],90)
        same = self.request('PATCH','/reservations/'+original['reference'],{'party_size':2},self.ada)[1]
        self.assertEqual(same,original)
        changed = self.request('PATCH','/reservations/'+original['reference'],{'party_size':1},self.ada)[1]
        self.assertEqual(changed['revision'],2)
        self.assertEqual(changed['accepted_terms']['policy_version'],2)
        self.assertEqual(changed['ends_at'][11:16],'20:00')
        self.assertEqual(self.history(original['reference'])[0]['accepted_terms']['policy_version'],0)
        self.assertEqual(self.request('POST','/reservations',self.booking(),self.ada,'new'),(200,original))
        nov = self.create('nov',starts_at_local='2032-11-01T19:00')
        self.assertEqual(nov['accepted_terms']['policy_version'],3)

    def test_policy_validation_permissions_and_idempotency(self):
        self.error(self.request('POST','/restaurants/r/policies',{},key='x'),401,'unauthenticated')
        self.error(self.request('POST','/restaurants/r/policies',{},self.ada,'x'),403,'forbidden')
        for change in [{'slot_minutes':True},{'slot_minutes':1441},{'reservation_duration_minutes':'60'},
                       {'cancellation_cutoff_minutes':10081},{'capacities':{'t1':2}},
                       {'opening_hours':[{'weekday':'mon','opens':'18:00','closes':'20:00'}]*2},
                       {'effective_from':'2032-02-30'}]:
            before = self.snapshot()
            self.error(self.request('POST','/restaurants/r/policies',self.policy(**change),self.bob,'x'),422,'validation_failed')
            self.assertEqual(before,self.snapshot())
        response = self.publish('x')
        self.assertEqual(response['policy_version'],1)
        self.assertEqual(self.request('POST','/restaurants/r/policies',self.policy(),self.bob,'x'),(200,response))
        self.error(self.request('POST','/restaurants/r/policies',{},self.bob,'x'),409,'idempotency_key_reuse')

    def test_explanations_report_independent_rules_and_policy(self):
        self.create()
        self.publish(capacities={'t1':1,'t2':4,'t3':6,'t4':8})
        path='/availability?restaurant_id=r&date=2032-10-25&party_size=2'
        normal=self.request('GET',path)[1]
        self.assertNotIn('explain',normal['slots'][0])
        for value in ['false','1','']:
            self.error(self.request('GET',path+'&explain='+value),422,'validation_failed')
        data=self.request('GET',path+'&explain=true')[1]
        slot=next(s for s in data['slots'] if s['starts_at_local'].endswith('19:00'))
        self.assertEqual(slot['explain'][0],{'table_id':'t1','policy_version':1,'available':False,
                         'rules':[{'rule':'capacity','holds':False},{'rule':'no_overlap','holds':False}]})
        self.assertEqual([e['table_id'] for e in slot['explain'] if e['available']],slot['available_table_ids'])
        self.assertEqual([e['table_id'] for e in slot['explain']],['t1','t2','t3','t4'])

    def test_history_pair_changes_privacy_revision_race(self):
        a=self.create()
        path='/reservations/'+a['reference']
        for suffix in ['/history','/decision']:
            for token in [None,self.bob,'unknown']:
                self.error(self.request('GET',path+suffix,token=token),404,'not_found')
        with ThreadPoolExecutor(max_workers=50) as pool:
            answers=list(pool.map(lambda _:self.request('PATCH',path,{'party_size':1,'expected_revision':1},self.ada),range(50)))
        self.assertEqual(sum(code==200 for code,_ in answers),1)
        self.assertEqual(sum(code==409 and body['error']['code']=='stale_revision' for code,body in answers),49)
        pair=self.request('PATCH',path,{'table_ids':['t1','t2'],'expected_revision':2},self.ada)[1]
        self.assertEqual(pair['revision'],3)
        self.assertEqual(pair['table_ids'],['t2','t1'])
        history=self.history(a['reference'])
        self.assertEqual(history[-1]['changes'],[{'field':'table_ids','from':['t1'],'to':['t2','t1']}])
        self.assertEqual(self.request('PATCH',path,{'table_ids':['t1','t2']},self.ada)[1],pair)
        self.assertEqual(self.history(a['reference']),history)
        cancelled=self.request('POST',path+'/cancel',{},self.ada)[1]
        self.assertEqual(cancelled['revision'],4)
        self.assertEqual(self.request('POST',path+'/cancel',{},self.ada)[1],cancelled)
        self.assertEqual([e['seq'] for e in self.history(a['reference'])],[1,2,3,4])
        self.assertEqual(self.history(a['reference'])[-1]['changes'],[])

    def test_series_anchor_terms_exceptions_moves_cancel_and_receipt(self):
        a=self.create()
        original_history=self.history(a['reference'])
        self.publish(effective_from='2032-11-01')
        series=self.adopt(a)
        self.assertEqual(series['occurrences'][0]['reservation'],a)
        self.assertEqual(self.history(a['reference']),original_history)
        self.assertEqual([o['reservation']['accepted_terms']['policy_version'] for o in series['occurrences']],[0,1,1])
        refs=[o['reference'] for o in series['occurrences']]
        for token in [None,self.bob]:
            self.error(self.request('GET','/series/'+series['series_id'],token=token),404,'not_found')
        self.error(self.request('POST','/series',{'anchor_reference':a['reference'],'count':2,'interval_weeks':1},self.ada,'another'),409,'already_in_series')
        before=self.snapshot()['state']['restaurant_revisions']['r']
        moves={'moves':[{'reference':ref,'party_size':1,'expected_revision':1} for ref in refs[1:]]}
        self.assertEqual(self.request('POST','/reservation-moves',moves,self.ada,'moves')[0],201)
        current=self.request('GET','/series/'+series['series_id'],token=self.ada)[1]
        self.assertEqual(current['revision'],2)
        self.assertEqual([o['exception'] for o in current['occurrences']],[False,True,True])
        self.assertEqual(self.snapshot()['state']['restaurant_revisions']['r'],before+1)
        self.request('POST','/reservations/'+refs[0]+'/cancel',{},self.ada)
        current=self.request('GET','/series/'+series['series_id'],token=self.ada)[1]
        self.assertEqual(current['revision'],3)
        self.assertFalse(current['occurrences'][0]['exception'])
        self.assertEqual(current['occurrences'][1]['reservation']['status'],'confirmed')
        self.assertEqual(self.request('POST','/series',{'anchor_reference':a['reference'],'count':3,'interval_weeks':1},self.ada,'series'),(200,series))

    def test_series_atomic_failure_dst_and_reusable_key(self):
        seed=fixture()
        seed['restaurants'][0]['opening_hours']=[{'weekday':d,'opens':'00:00','closes':'06:00'} for d in base.fixture()['restaurants'][0]['opening_hours'] for d in [d['weekday']]]
        self.request('POST','/_test/reset',seed); self.ada=self.login('ada')
        a=self.create(starts_at_local='2032-03-21T02:30')
        before=self.snapshot()
        self.error(self.request('POST','/series',{'anchor_reference':a['reference'],'count':3,'interval_weeks':1},self.ada,'series'),422,'invalid_local_time')
        self.assertEqual(before,self.snapshot())
        self.request('PATCH','/reservations/'+a['reference'],{'starts_at_local':'2032-03-21T03:30'},self.ada)
        self.adopt(a)

    def test_populated_snapshot_history_series_and_invalid_import(self):
        a=self.create(); self.publish(); series=self.adopt(a)
        ref=series['occurrences'][1]['reference']
        self.request('PATCH','/reservations/'+ref,{'table_ids':['t1','t2']},self.ada)
        self.request('POST','/reservations/'+series['occurrences'][2]['reference']+'/cancel',{},self.ada)
        snapshot=self.snapshot()
        self.assertEqual(self.request('POST','/_test/import',snapshot,server=1)[0],204)
        self.assertEqual(snapshot,self.snapshot(server=1))
        self.assertEqual(self.request('POST','/series',{'anchor_reference':a['reference'],'count':3,'interval_weeks':1},self.ada,'series',server=1),(200,series))
        corrupt=copy.deepcopy(snapshot); corrupt['state']['histories'][ref][-1]['changes'][0]['from']=['t4']
        self.error(self.request('POST','/_test/import',corrupt,server=1),422,'validation_failed')
        self.assertEqual(snapshot,self.snapshot(server=1))

    def test_real_stage1_and_stage2_upgrade_then_adoption(self):
        for stage in (1,2):
            self.urls.append(os.environ['TABLEKEEPER_STAGE'+str(stage)+'_URL'])
            index=len(self.urls)-1
            seed=base.fixture() if stage==1 else pair_fixture()
            self.assertEqual(self.request('POST','/_test/reset',seed,server=index)[0],204)
            token=self.login('ada',server=index)
            body=self.booking()
            if stage==2:
                body.pop('table_id'); body['table_ids']=['t2','t1']
            status,original=self.request('POST','/reservations',body,token,'original',server=index)
            self.assertEqual(status,201)
            exported=self.snapshot(server=index)
            self.assertEqual(self.request('POST','/_test/import',exported)[0],204)
            self.assertEqual(self.request('POST','/reservations',body,token,'original'),(200,original))
            self.ada=token
            adopted=self.adopt(original,key='adopt'+str(stage))
            self.assertEqual(len(adopted['occurrences']),3)
            self.assertEqual(self.request('POST','/_test/import',self.snapshot(),server=1)[0],204)


if __name__ == '__main__': unittest.main(verbosity=2)
