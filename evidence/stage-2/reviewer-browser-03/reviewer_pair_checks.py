"""Independent Stage2 API/upgrade cases, authored before implementation inspection."""
import copy
import json
import os
import unittest
import reviewer_inherited as inherited

request=inherited.request
BASE=inherited.BASE
DEST=inherited.DEST
OLD=os.environ.get('REVIEW_OLD','http://127.0.0.1:18084')
DAY=inherited.FUTURE

def pair_fixture():
    f=inherited.fixture(tables=4)
    r=f['restaurants'][0]
    r['tables']=[dict(id=t,label=label,capacity=c) for t,label,c in [
        ('c','Garden alcove',4),('a','Window nook',2),('d','Chef counter',5),('b','Courtyard',3)]]
    r['combinable']=[['b','a'],['c','b'],['a','d']]
    return f

class PairChecks(unittest.TestCase):
    reset=inherited.SpecChecks.reset
    login=inherited.SpecChecks.login
    err=inherited.SpecChecks.err
    listing=inherited.SpecChecks.listing
    availability=inherited.SpecChecks.availability
    burst=inherited.SpecChecks.burst

    def setUp(self):
        self.seed=pair_fixture();self.reset(self.seed)
        self.tokens=[self.login(i) for i in range(2)]

    def body(self, tables=('b','a'), local=DAY+'T18:00', size=4):
        return dict(restaurant_id='r',table_ids=list(tables),starts_at_local=local,party_size=size)

    def create(self,tables=('b','a'),local=DAY+'T18:00',size=4,key='pair',base=BASE):
        body=self.body(tables,local,size)
        status,value=request('POST','/reservations',body,self.tokens[0],key,base=base)
        self.assertEqual(status,201)
        self.assertEqual(value['table_ids'],list(tables))
        if len(tables)==1:self.assertEqual(value['table_id'],tables[0])
        else:self.assertNotIn('table_id',value)
        return value

    def test_pair_01_options_exact_order_and_capacity(self):
        tables=self.seed['restaurants'][0]['tables'];pairs=self.seed['restaurants'][0]['combinable']
        cap={t['id']:t['capacity'] for t in tables}
        for party in range(1,11):
            with self.subTest(party=party):
                expected=[dict(table_ids=[t['id']],capacity=t['capacity']) for t in tables if t['capacity']>=party]
                expected += [dict(table_ids=p,capacity=sum(cap[t] for t in p)) for p in pairs if sum(cap[t] for t in p)>=party]
                for slot in self.availability(size=party):
                    self.assertEqual(slot['available_options'],expected)
                    self.assertEqual(slot['available_table_ids'],[t['id'] for t in tables if t['capacity']>=party])

    def test_pair_02_validation_keys_and_canonical_order(self):
        cases=[(dict(self.body(),table_id='a'),'validation_failed'),
               (self.body(['a','a']),'validation_failed'),(self.body([]),'validation_failed'),
               (self.body(['a','b','c']),'combination_not_allowed'),
               (self.body(['a','c']),'combination_not_allowed'),
               (self.body(size=6),'party_exceeds_capacity')]
        for body,code in cases:
            self.err('POST','/reservations',body,422,code,key='reusable')
            self.assertEqual(self.listing(),[])
        for ids in ['a',1,True,{},None]:
            self.err('POST','/reservations',dict(self.body(),table_ids=ids),400,'malformed_request')
        self.err('POST','/reservations',self.body(['a','unknown']),404,'not_found')
        body=self.body(['a','b'])
        status,record=request('POST','/reservations',body,self.tokens[0],'reusable')
        self.assertEqual(status,201);self.assertEqual(record['table_ids'],['b','a'])
        self.assertNotIn('table_id',record)
        self.assertEqual(request('POST','/reservations',body,self.tokens[0],'reusable'),(200,record))
        self.err('POST','/reservations',self.body(['b','a']),409,'idempotency_key_reuse',key='reusable')

    def test_pair_03_occupancy_adjacency_and_cancelled_seed(self):
        record=self.create()
        for ids in [['a'],['b'],['c','b'],['a','d']]:
            self.err('POST','/reservations',self.body(ids,size=2),409,'table_unavailable')
        self.create(['c'],size=2,key='disjoint')
        self.create(local=DAY+'T19:30',key='adjacent')
        slot=self.availability()[0]
        self.assertEqual(slot['available_table_ids'],['d'])
        self.assertEqual(slot['available_options'],[dict(table_ids=['d'],capacity=5)])
        request('POST','/reservations/'+record['reference']+'/cancel',{},self.tokens[0])
        self.assertIn(dict(table_ids=['b','a'],capacity=5),self.availability()[0]['available_options'])
        seed=pair_fixture();seed['reservations']=[dict(self.body(),id='seed-pair',reference='PAIRSEED',user_id='u0',status='cancelled')]
        self.reset(seed);self.tokens=[self.login(i) for i in range(2)]
        self.assertEqual(self.listing()[0]['status'],'cancelled')
        self.assertEqual(self.listing()[0]['table_ids'],['b','a'])
        self.assertIn(dict(table_ids=['b','a'],capacity=5),self.availability(size=4)[0]['available_options'])
        self.create(key='seed-does-not-occupy')

    def test_pair_04_patch_transitions_and_failed_atomicity(self):
        a=self.create(['c'],size=4)
        path='/reservations/'+a['reference']
        status,pair=request('PATCH',path,{'table_ids':['a','b']},self.tokens[0])
        self.assertEqual(status,200);self.assertEqual(pair['table_ids'],['b','a']);self.assertNotIn('table_id',pair)
        for field in ['reference','reservation_id','created_at']:self.assertEqual(pair[field],a[field])
        self.assertEqual(request('PATCH',path,{'table_ids':['a','b'],'ignored':True},self.tokens[0]),(200,pair))
        blocker=self.create(['d'],size=1,key='blocker')
        before=self.listing()
        self.err('PATCH',path,{'table_ids':['d'],'party_size':2},409,'table_unavailable')
        self.assertEqual(self.listing(),before)
        status,single=request('PATCH',path,{'table_id':'c'},self.tokens[0])
        self.assertEqual(status,200);self.assertEqual(single['table_ids'],['c']);self.assertEqual(single['table_id'],'c')

    def test_pair_05_batch_swap_rollback_and_receipt(self):
        seed=pair_fixture();seed['restaurants'][0]['combinable'].append(['c','d']);self.reset(seed);self.tokens=[self.login(i) for i in range(2)]
        a=self.create();b=self.create(['c','d'],key='second')
        moves={'moves':[{'reference':a['reference'],'table_ids':['d','c']},{'reference':b['reference'],'table_ids':['a','b']}]}
        status,receipt=request('POST','/reservation-moves',moves,self.tokens[0],'swap')
        self.assertEqual(status,201);self.assertEqual([r['table_ids'] for r in receipt['reservations']],[['c','d'],['b','a']])
        before=self.listing()
        self.err('POST','/reservation-moves',{'moves':[{'reference':a['reference'],'table_ids':['a','b']},{'reference':b['reference']}]},409,'table_unavailable',key='failed')
        self.assertEqual(self.listing(),before)
        self.assertEqual(request('POST','/reservation-moves',moves,self.tokens[0],'swap'),(200,receipt))
        request('POST','/reservations/'+a['reference']+'/cancel',{},self.tokens[0])
        self.assertEqual(request('POST','/reservation-moves',moves,self.tokens[0],'swap'),(200,receipt))

    def test_pair_06_fifty_conflicts_and_fifty_identical(self):
        results=self.burst(lambda i:request('POST','/reservations',self.body(['b','a'] if i%2==0 else ['a'],size=2),self.tokens[0],'conflict'+str(i)))
        self.assertEqual(sum(s==201 for s,v in results),1)
        self.assertEqual(sum(s==409 and v['error']['code']=='table_unavailable' for s,v in results),49)
        self.assertEqual(len(self.listing()),1)
        self.reset(self.seed);self.tokens=[self.login(i) for i in range(2)]
        results=self.burst(lambda i:request('POST','/reservations',self.body(),self.tokens[0],'identical'))
        self.assertEqual(sum(s==201 for s,v in results),1);self.assertEqual(sum(s==200 for s,v in results),49)
        self.assertTrue(all(v==results[0][1] for s,v in results));self.assertEqual(len(self.listing()),1)

    def test_pair_07_pair_snapshot_replacement(self):
        row=self.create();original=self.body();token2=self.login()
        moves={'moves':[{'reference':row['reference'],'table_ids':['c'],'party_size':3}]}
        status,batch=request('POST','/reservation-moves',moves,self.tokens[0],'batch');self.assertEqual(status,201)
        request('POST','/reservations/'+row['reference']+'/cancel',{},self.tokens[0])
        expected=self.listing();snapshot=request('GET','/_test/export')[1]
        self.reset(self.seed,base=DEST);old_destination=self.login(base=DEST)
        for repeat in range(2):
            self.assertEqual(request('POST','/_test/import',snapshot,base=DEST),(204,None))
            for token in [self.tokens[0],token2]:self.assertEqual(self.listing(base=DEST,token=token),expected)
            self.assertEqual(request('POST','/reservations',original,self.tokens[0],'pair',base=DEST),(200,row))
            self.assertEqual(request('POST','/reservation-moves',moves,self.tokens[0],'batch',base=DEST),(200,batch))
            self.err('GET','/reservations',None,401,'unauthenticated',token=old_destination,base=DEST)
        self.assertEqual(self.login(base=DEST) is not None,True)

    def test_pair_08_actual_stage1_upgrade_original_receipts(self):
        self.reset(inherited.fixture(),base=OLD)
        token=self.login(base=OLD);second=self.login(base=OLD)
        body=dict(restaurant_id='r',table_id='t1',starts_at_local=DAY+'T18:00',party_size=3,ignored={'kept':True})
        status,receipt=request('POST','/reservations',body,token,'old-create',base=OLD);self.assertEqual(status,201)
        self.assertNotIn('table_ids',receipt)
        moves={'moves':[{'reference':receipt['reference'],'table_id':'t2'}]}
        status,batch=request('POST','/reservation-moves',moves,token,'old-move',base=OLD);self.assertEqual(status,201)
        request('POST','/reservations/'+receipt['reference']+'/cancel',{},token,base=OLD)
        before=request('GET','/reservations',token=token,base=OLD)[1]
        snapshot=request('GET','/_test/export',base=OLD)[1]
        self.reset(pair_fixture(),base=DEST);obsolete=self.login(base=DEST)
        self.assertEqual(request('POST','/_test/import',snapshot,base=DEST),(204,None))
        for t in [token,second]:
            got=request('GET','/reservations',token=t,base=DEST)[1]['reservations']
            self.assertEqual([{k:r[k] for k in before['reservations'][0]} for r in got],before['reservations'])
        self.assertEqual(request('POST','/reservations',body,token,'old-create',base=DEST),(200,receipt))
        self.assertEqual(request('POST','/reservation-moves',moves,token,'old-move',base=DEST),(200,batch))
        self.err('GET','/reservations',None,401,'unauthenticated',token=obsolete,base=DEST)
        self.login(base=DEST)
        self.assertEqual(request('POST','/_test/import',{'track':'tablekeeper','format_version':1,'state':{}},base=DEST)[0],422)
        self.assertEqual(request('POST','/reservations',body,token,'old-create',base=DEST),(200,receipt))
