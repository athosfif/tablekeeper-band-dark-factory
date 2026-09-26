"""Stage4 operations after real earlier-service imports; snapshots stay in memory."""
import copy
import datetime as dt
import os
import unittest
import reviewer_inherited as api
from reviewer_replan_checks import ReplanChecks,closure_fixture,request

class FinalUpgradeChecks(unittest.TestCase):
    reset=ReplanChecks.reset;login=ReplanChecks.login;err=ReplanChecks.err
    body=ReplanChecks.body;closure=ReplanChecks.closure

    def setUp(self):
        self.seed=closure_fixture()

    def test_final_upgrade_01_actual_stage3_series_and_all_receipts(self):
        old=os.environ['REVIEW_OLD3'];self.reset(self.seed,base=old)
        token=self.login(base=old);second=self.login(base=old)
        def oldcall(method,path,body=None,key=None):return request(method,path,body,token,key,base=old)
        create=self.body('t0',party=2)
        status,anchor=oldcall('POST','/reservations',create,'anchor');self.assertEqual(status,201)
        adoption=dict(anchor_reference=anchor['reference'],count=4,interval_weeks=1)
        status,original=oldcall('POST','/series',adoption,'adopt');self.assertEqual(status,201)
        sid=original['series_id'];rows=[o['reservation'] for o in original['occurrences']]
        shifted=(dt.date.fromisoformat(rows[1]['starts_at_local'][:10])+dt.timedelta(days=1)).isoformat()+'T18:00'
        self.assertEqual(oldcall('PATCH','/reservations/'+rows[1]['reference'],dict(table_id='t2',starts_at_local=shifted))[0],200)
        self.assertEqual(oldcall('POST','/reservations/'+rows[2]['reference']+'/cancel',{})[0],200)
        moves={'moves':[{'reference':rows[3]['reference'],'table_id':'t1'}]}
        status,moved=oldcall('POST','/reservation-moves',moves,'moved');self.assertEqual(status,201)
        expected=oldcall('GET','/series/'+sid)[1]
        histories={o['reference']:oldcall('GET','/reservations/'+o['reference']+'/history')[1] for o in expected['occurrences']}
        snapshot=request('GET','/_test/export',base=old)[1]
        oldcall('POST','/reservations/'+anchor['reference']+'/cancel',{})
        self.reset(base=api.DEST);displaced=self.login(base=api.DEST)
        self.assertEqual(request('POST','/_test/import',snapshot,base=api.DEST)[0],204)
        def call(method,path,body=None,key=None):return request(method,path,body,token,key,base=api.DEST)
        self.assertEqual(call('GET','/series/'+sid),(200,expected))
        self.assertEqual(request('GET','/series/'+sid,token=second,base=api.DEST),(200,expected))
        self.assertEqual(request('GET','/reservations',token=displaced,base=api.DEST)[0],401)
        for ref,h in histories.items():self.assertEqual(call('GET','/reservations/'+ref+'/history'),(200,h))
        for path,body,key,response in [('/reservations',create,'anchor',anchor),('/series',adoption,'adopt',original),('/reservation-moves',moves,'moved',moved)]:
            self.assertEqual(call('POST',path,body,key),(200,response))
        closure=self.closure()
        status,plan=call('POST','/restaurants/r/replans',closure,'plan');self.assertEqual(status,201)
        self.assertEqual(plan['moved_count'],1)
        applypath='/restaurants/r/replans/'+plan['plan_id']+'/apply'
        status,applied=call('POST',applypath,{},'apply');self.assertEqual(status,201)
        afterplan=call('GET','/series/'+sid)[1]
        self.assertEqual(afterplan['revision'],expected['revision']+1)
        self.assertEqual([o['exception'] for o in afterplan['occurrences']],[False,True,False,True])
        amend=dict(expected_revision=afterplan['revision'],from_index=0,local_time='19:00')
        status,amended=call('POST','/series/'+sid+'/amend',amend,'amend');self.assertEqual(status,201)
        self.assertEqual(amended['occurrences'][0]['reservation']['starts_at_local'],api.FUTURE+'T19:00')
        self.assertEqual(amended['occurrences'][1:],afterplan['occurrences'][1:])
        # Carry the populated Stage4 result, plans, receipts and histories to another container.
        stage4snapshot=request('GET','/_test/export',base=api.DEST)[1]
        self.reset(self.seed);evicted=self.login()
        self.assertEqual(request('POST','/_test/import',stage4snapshot)[0],204)
        self.assertEqual(request('GET','/reservations',token=evicted)[0],401)
        for repeat in range(2):
            self.assertEqual(request('POST','/_test/import',stage4snapshot)[0],204)
            self.assertEqual(request('GET','/series/'+sid,token=token),(200,amended))
            for path,body,key,response in [('/reservations',create,'anchor',anchor),('/series',adoption,'adopt',original),('/reservation-moves',moves,'moved',moved),('/restaurants/r/replans',closure,'plan',plan),(applypath,{},'apply',applied),('/series/'+sid+'/amend',amend,'amend',amended)]:
                self.assertEqual(request('POST',path,body,token,key),(200,response))
            status,failure=request('POST',applypath,{},token,'different-apply')
            self.assertEqual((status,failure['error']['code']),(409,'plan_already_applied'))
            for o in amended['occurrences']:
                path='/reservations/'+o['reference']+'/history'
                self.assertEqual(request('GET',path,token=token),call('GET',path))

    def test_final_upgrade_02_stages1_and2_imported_anchor_uses_new_operations(self):
        for stage,base in [(1,os.environ['REVIEW_OLD']),(2,os.environ['REVIEW_OLD2'])]:
            with self.subTest(stage=stage):
                self.reset(self.seed,base=base);token=self.login(base=base)
                body=self.body('t0',party=2)
                status,original=request('POST','/reservations',body,token,'old-anchor',base=base);self.assertEqual(status,201)
                snapshot=request('GET','/_test/export',base=base)[1]
                self.reset(self.seed);self.assertEqual(request('POST','/_test/import',snapshot)[0],204)
                self.assertEqual(request('POST','/reservations',body,token,'old-anchor'),(200,original))
                adoption=dict(anchor_reference=original['reference'],count=3,interval_weeks=1)
                status,series=request('POST','/series',adoption,token,'adopt');self.assertEqual(status,201)
                # Earlier schemas do not grant manager roles. Exercise owner-only
                # new operations here; manager repair is covered by Stage3 imports.
                current=request('GET','/series/'+series['series_id'],token=token)[1]
                status,result=request('POST','/series/'+series['series_id']+'/amend',dict(expected_revision=current['revision'],from_index=0,local_time='19:00'),token,'amend')
                self.assertEqual(status,201);self.assertEqual(len(result['occurrences']),3)
                self.assertTrue(all(o['reservation']['starts_at_local'].endswith('T19:00') for o in result['occurrences']))
                self.assertEqual(request('POST','/reservations',body,token,'old-anchor'),(200,original))

    def test_final_upgrade_03_unapplied_plan_survives_snapshot_replacement(self):
        self.reset(self.seed);token=self.login()
        status,row=request('POST','/reservations',self.body('t0',party=2),token,'book');self.assertEqual(status,201)
        closure=self.closure();status,plan=request('POST','/restaurants/r/replans',closure,token,'plan');self.assertEqual(status,201)
        snapshot=request('GET','/_test/export')[1]
        self.reset(base=api.DEST);self.assertEqual(request('POST','/_test/import',snapshot,base=api.DEST)[0],204)
        path='/restaurants/r/replans/'+plan['plan_id']+'/apply'
        status,applied=request('POST',path,{},token,'apply',base=api.DEST);self.assertEqual(status,201)
        self.assertEqual(applied['restaurant_revision'],plan['restaurant_revision']+1)
        self.assertEqual(request('GET','/reservations/'+row['reference'],token=token)[1],row)
        self.assertEqual(request('POST','/_test/import',snapshot,base=api.DEST)[0],204)
        self.assertEqual(request('POST',path,{},token,'apply-again',base=api.DEST)[0],201)
