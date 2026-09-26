"""Specification-derived HTTP acceptance; stdlib only, no implementation imports.

REVIEW_BASE and REVIEW_DEST must point to independent, disposable service processes.
Run: python reviewer_spec_checks.py -v
No exports, passwords, or tokens are printed or written by this suite.
"""
import concurrent.futures
import copy
import datetime as dt
import json
import os
import re
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

BASE = os.environ.get('REVIEW_BASE', 'http://127.0.0.1:18081')
DEST = os.environ.get('REVIEW_DEST', 'http://127.0.0.1:18082')
FUTURE = '2040-06-14'
PASSWORD = 'synthetic reviewer password'
METRICS = []


def fixture(zone='UTC', opens='18:00', closes='23:00', duration=90, slot=30, tables=10):
    r = dict(id='r', name='Review café', timezone=zone, slot_minutes=slot,
             reservation_duration_minutes=duration, cancellation_cutoff_minutes=120,
             opening_hours=[dict(weekday=d, opens=opens, closes=closes)
                            for d in ['thu', 'mon', 'sun', 'sat', 'wed', 'tue', 'fri']],
             tables=[dict(id='t'+str(i), label=str(i), capacity=2 if i == 0 else 8)
                     for i in range(tables)])
    r2 = copy.deepcopy(r)
    r2.update(id='other', name='Other', tables=[dict(id='other_table', label='other', capacity=8)])
    return dict(users=[dict(id='u'+str(i), email=f'reviewer{i}@example.test',
                            password=PASSWORD, display_name='Reviewer '+str(i)) for i in range(2)],
                restaurants=[r, r2], reservations=[])


def request(method, path, body=None, token=None, key=None, base=BASE, raw=None, auth=None, parse_json=True):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    if token: headers['Authorization'] = 'Bearer '+token
    if auth is not None: headers['Authorization'] = auth
    if key is not None: headers['Idempotency-Key'] = key
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    start = time.monotonic()
    try:
        response = urllib.request.urlopen(urllib.request.Request(base+path, data=data, headers=headers,
                                                                  method=method), timeout=10 if path.startswith('/_test/') else 5)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        status = response.status
        content_type = response.headers.get('Content-Type', '')
        content = response.read()
    elapsed = time.monotonic()-start
    METRICS.append((method, path.split('?')[0], status, elapsed))
    assert status < 500, f'{method} {path} returned {status}'
    assert elapsed < (10 if path.startswith('/_test/') else 5), f'{method} {path} timeout {elapsed}'
    if status == 204:
        assert content == b'', '204 must have no content'
        return status, None
    assert 'application/json' in content_type.lower() and 'charset=utf-8' in content_type.lower().replace(' ', ''), content_type
    if not parse_json:
        assert status==200
        return status,content
    value = json.loads(content)
    if status >= 400:
        assert isinstance(value.get('error'), dict), 'missing error object'
        assert isinstance(value['error'].get('code'), str)
        assert isinstance(value['error'].get('message'), str) and value['error']['message']
    return status, value


class SpecChecks(unittest.TestCase):
    def setUp(self):
        self.seed = fixture()
        self.reset(self.seed)
        self.tokens = [self.login(i) for i in range(2)]

    def reset(self, value=None, base=BASE):
        self.assertEqual(request('POST', '/_test/reset', value or fixture(), base=base)[0], 204)

    def login(self, i=0, base=BASE):
        status, value = request('POST', '/auth/login', dict(email=f'reviewer{i}@example.test', password=PASSWORD), base=base)
        self.assertEqual(status, 200)
        self.assertEqual(value['user_id'], 'u'+str(i))
        self.assertEqual(value['display_name'], 'Reviewer '+str(i))
        self.assertTrue(isinstance(value['token'], str) and value['token'])
        return value['token']

    def body(self, table='t1', local=FUTURE+'T18:00', **extra):
        return dict(restaurant_id='r', table_id=table, starts_at_local=local, party_size=2, **extra)

    def book(self, table='t1', local=FUTURE+'T18:00', key=None, user=0):
        body = self.body(table, local)
        status, value = request('POST', '/reservations', body, self.tokens[user], key or table+local)
        self.assertEqual(status, 201)
        self.assertRegex(value['reference'], r'^[A-Z0-9]{6,12}$')
        self.assertLessEqual(len(value['reservation_id']), 64)
        for field in ('starts_at', 'ends_at', 'created_at'):
            self.assertIsNotNone(dt.datetime.fromisoformat(value[field]).utcoffset())
        return value

    def err(self, method, path, body, status, code, key='invalid', token='default', base=BASE, **kw):
        if token == 'default': token = self.tokens[0]
        actual, value = request(method, path, body, token, key, base=base, **kw)
        self.assertEqual((actual, value.get('error', {}).get('code')), (status, code))

    def listing(self, base=BASE, token=None):
        status, value = request('GET', '/reservations', token=token or self.tokens[0], base=base)
        self.assertEqual(status, 200)
        return value['reservations']

    def availability(self, date=FUTURE, size=2, base=BASE):
        status, value = request('GET', '/availability?'+urllib.parse.urlencode(dict(restaurant_id='r', date=date, party_size=size, ignored='yes')), base=base)
        self.assertEqual(status, 200)
        return value['slots']

    def burst(self, action, count=50):
        barrier = threading.Barrier(count)
        def run(i):
            barrier.wait(timeout=15)
            return action(i)
        with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
            return list(pool.map(run, range(count)))

    def test_01_public_configuration_and_seed(self):
        self.assertEqual(request('GET', '/health'), (200, {'status': 'ok'}))
        status, restaurants = request('GET', '/restaurants?unknown=1')
        self.assertEqual(status, 200)
        self.assertEqual([r['id'] for r in restaurants['restaurants']], ['r', 'other'])
        self.assertEqual(request('GET', '/restaurants/r')[1], self.seed['restaurants'][0])
        self.err('GET', '/restaurants/nope', None, 404, 'not_found', token=None)
        slots = self.availability()
        self.assertEqual([s['starts_at_local'] for s in slots], [FUTURE+'T'+t for t in ['18:00','18:30','19:00','19:30','20:00','20:30','21:00','21:30']])
        self.assertEqual(slots[0]['available_table_ids'], ['t'+str(i) for i in range(10)])
        self.assertEqual(self.availability(size=3)[0]['available_table_ids'], ['t'+str(i) for i in range(1,10)])
        self.assertEqual(self.availability(size=9)[0]['available_table_ids'], [])
        self.seed['restaurants'][0]['opening_hours'] = []
        self.reset(self.seed)
        self.assertEqual(self.availability(), [])

    def test_02_authentication_and_sessions(self):
        signup = dict(email='new@example.test', password='abcdefgh', display_name='New', ignored={'x': True})
        status, account = request('POST', '/auth/signup', signup)
        self.assertEqual(status, 201)
        self.assertLessEqual(len(account['user_id']), 64)
        self.err('POST', '/auth/signup', signup, 409, 'email_taken', token=None)
        self.err('POST', '/auth/signup', dict(signup, email='bad'), 422, 'validation_failed', token=None)
        self.err('POST', '/auth/signup', dict(signup, email='short@example.test', password='1234567'), 422, 'validation_failed', token=None)
        self.err('POST', '/auth/login', dict(email='absent@example.test', password=PASSWORD), 401, 'unauthenticated', token=None)
        self.err('POST', '/auth/login', dict(email='reviewer0@example.test', password='wrong'), 401, 'unauthenticated', token=None)
        token2 = self.login()
        for token in [self.tokens[0], token2, account['token']]:
            self.assertEqual(self.listing(token=token), [])
        for method, path, body in [('GET','/reservations',None), ('GET','/reservations/ABSENT',None), ('PATCH','/reservations/ABSENT',{}), ('POST','/reservations/ABSENT/cancel',{}), ('POST','/reservations',self.body()), ('POST','/reservation-moves',{'moves':[]})]:
            for auth in [None, 'Token abc', 'Bearer unknown', 'Bearer']:
                with self.subTest(method=method,path=path,auth=auth):
                    self.err(method,path,body,401,'unauthenticated',token=None,auth=auth)

    def test_03_type_format_and_missing_errors(self):
        for raw in [b'{', b'[]', b'null', b'1']:
            with self.subTest(raw=raw): self.err('POST','/reservations',None,400,'malformed_request',raw=raw)
        for field in ['restaurant_id','table_id','starts_at_local','party_size']:
            body=self.body(); del body[field]
            with self.subTest(missing=field): self.err('POST','/reservations',body,422,'validation_failed')
        for field in ['restaurant_id','table_id','starts_at_local']:
            for wrong in [True, 1, [], {}, None]:
                with self.subTest(field=field,wrong=wrong): self.err('POST','/reservations',dict(self.body(),**{field:wrong}),400,'malformed_request')
        for wrong in [0,-1,1.5,True,False,'2',[],{},None]:
            with self.subTest(party_size=wrong): self.err('POST','/reservations',dict(self.body(),party_size=wrong),422,'validation_failed')
        for wrong in ['2040-02-30T18:00','2040-06-14T18:00Z','2040-06-14T18:00+00:00','2040-06-14T18:00:00','2040-6-14T18:00','2040-06-14 18:00','']:
            with self.subTest(local=wrong): self.err('POST','/reservations',dict(self.body(),starts_at_local=wrong),422,'validation_failed')
        for key in [None,'']:
            self.err('POST','/reservations',self.body(),400,'missing_idempotency_key',key=key)
        self.err('POST','/reservations',self.body(),422,'validation_failed',key='x'*256)
        self.book(key='x'*255)
        for field in ['email','password','display_name']:
            body=dict(email='another@example.test',password=PASSWORD,display_name='A'); body[field]=[]
            self.err('POST','/auth/signup',body,400,'malformed_request',token=None)
        for size in ['1e9','4.0','+4','-1','0','true','']:
            self.err('GET','/availability?'+urllib.parse.urlencode(dict(restaurant_id='r',date=FUTURE,party_size=size)),None,422,'validation_failed',token=None)
        for missing in ['restaurant_id','date','party_size']:
            query=dict(restaurant_id='r',date=FUTURE,party_size='2'); del query[missing]
            self.err('GET','/availability?'+urllib.parse.urlencode(query),None,422,'validation_failed',token=None)
        for date in ['2040-02-30','2040-1-01','2040-06-14T18:00']:
            self.err('GET','/availability?'+urllib.parse.urlencode(dict(restaurant_id='r',date=date,party_size=2)),None,422,'validation_failed',token=None)

    def test_04_past_dates_seed_ids_and_reset(self):
        old=self.book(local='2000-02-29T18:00')
        self.err('POST','/reservations/'+old['reference']+'/cancel',{},409,'cutoff_passed')
        seed=fixture(); seed['users'][0]['id']='u'*64; seed['restaurants'][0]['id']='r'*64
        seed['restaurants'][0]['tables'][0]['id']='t'*64
        seed['reservations']=[dict(restaurant_id='r'*64,table_id='t'*64,starts_at_local=FUTURE+'T18:00',party_size=2,id='b'*64,reference='SEED01',user_id='u'*64)]
        self.reset(seed)
        status,login=request('POST','/auth/login',dict(email='reviewer0@example.test',password=PASSWORD)); self.assertEqual(status,200)
        record=request('GET','/reservations/SEED01',token=login['token'])[1]
        self.assertEqual(record['reservation_id'],'b'*64)
        self.err('GET','/reservations',None,401,'unauthenticated',token=self.tokens[0])
        self.reset(); self.reset()
        self.err('GET','/reservations',None,401,'unauthenticated',token=login['token'])

    def test_05_create_errors_and_half_open(self):
        for change,status,code in [({'table_id':'missing'},404,'not_found'),({'restaurant_id':'missing'},404,'not_found'),({'table_id':'other_table'},404,'not_found'),({'table_id':'t0','party_size':3},422,'party_exceeds_capacity'),({'starts_at_local':FUTURE+'T18:01'},422,'not_on_slot_grid'),({'starts_at_local':FUTURE+'T17:30'},422,'outside_opening_hours'),({'starts_at_local':FUTURE+'T22:00'},422,'outside_opening_hours')]:
            with self.subTest(change=change): self.err('POST','/reservations',dict(self.body(),**change),status,code)
        first=self.book(); second=self.book(local=FUTURE+'T19:30')
        self.assertNotEqual(first['reference'],second['reference'])
        self.err('POST','/reservations',self.body(local=FUTURE+'T19:00'),409,'table_unavailable')
        self.assertNotIn('t1',self.availability()[0]['available_table_ids'])
        self.assertIn('t1',next(s for s in self.availability() if s['starts_at_local'].endswith('21:00'))['available_table_ids'])
        # Failed conflict does not burn its key.
        self.assertEqual(request('POST','/reservations',self.body('t2'),self.tokens[0],'invalid')[0],201)

    def test_06_parsed_json_idempotency_and_receipts(self):
        original=dict(self.body(),ignored={'truth':True,'array':[1,{'z':'é'}]})
        status,receipt=request('POST','/reservations',original,self.tokens[0],'shared'); self.assertEqual(status,201)
        raw=json.dumps(dict(reversed(list(original.items()))),ensure_ascii=False,indent=2).encode()
        self.assertEqual(request('POST','/reservations',token=self.tokens[0],key='shared',raw=raw),(200,receipt))
        for body in [dict(original,party_size=False),dict(original,table_id='missing'),dict(original,ignored={'truth':1,'array':[1,{'z':'é'}]}),dict(original,ignored={'truth':True,'array':[1,{'z':'changed'}]}),{},dict(original,party_size=[]),dict(original,table_id=None)]:
            with self.subTest(body_kind=list(body)): self.err('POST','/reservations',body,409,'idempotency_key_reuse',key='shared')
        self.err('POST','/reservations',None,400,'malformed_request',key='shared',raw=b'[]')
        self.err('POST','/reservations',original,401,'unauthenticated',key='shared',token=None)
        self.assertEqual(request('POST','/reservations',self.body('t2'),self.tokens[1],'shared')[0],201)
        moves={'moves':[{'reference':receipt['reference'],'table_id':'t3'}]}
        status,batch=request('POST','/reservation-moves',moves,self.tokens[0],'shared'); self.assertEqual(status,201)
        self.assertEqual(request('POST','/reservations',original,self.tokens[0],'shared'),(200,receipt))
        self.assertEqual(request('POST','/reservations/'+receipt['reference']+'/cancel',{},self.tokens[0])[0],200)
        self.assertEqual(request('POST','/reservations',original,self.tokens[0],'shared'),(200,receipt))
        self.assertEqual(request('POST','/reservation-moves',moves,self.tokens[0],'shared'),(200,batch))
        self.assertEqual(self.listing()[0]['status'],'cancelled')

    def test_07_50_concurrent_unique_create_contention(self):
        results=self.burst(lambda i:request('POST','/reservations',self.body(),self.tokens[0],'contend-'+str(i)))
        self.assertEqual([s for s,_ in results].count(201),1)
        self.assertEqual([s for s,_ in results].count(409),49)
        self.assertTrue(all(s==201 or b['error']['code']=='table_unavailable' for s,b in results))
        self.assertEqual(len(self.listing()),1)

    def test_08_50_concurrent_identical_create(self):
        results=self.burst(lambda i:request('POST','/reservations',self.body(),self.tokens[0],'one'))
        self.assertEqual([s for s,_ in results].count(201),1)
        self.assertEqual([s for s,_ in results].count(200),49)
        self.assertTrue(all(b==results[0][1] for _,b in results)); self.assertEqual(len(self.listing()),1)

    def test_09_list_privacy_patch_cancel(self):
        early=self.book(); late=self.book('t2',FUTURE+'T20:00'); other=self.book('t3',user=1)
        self.assertEqual(self.listing(),[late,early])
        for method,suffix,body in [('GET','',None),('PATCH','',{'party_size':3}),('POST','/cancel',{})]:
            self.err(method,'/reservations/'+other['reference']+suffix,body,404,'not_found')
        self.assertEqual(request('PATCH','/reservations/'+early['reference'],{'ignored':'x'},self.tokens[0]),(200,early))
        self.err('PATCH','/reservations/'+early['reference'],{'table_id':'t2','starts_at_local':FUTURE+'T20:00'},409,'table_unavailable')
        self.assertEqual(request('GET','/reservations/'+early['reference'],token=self.tokens[0]),(200,early))
        status,moved=request('PATCH','/reservations/'+early['reference'],{'table_id':'t4','party_size':5},self.tokens[0]); self.assertEqual(status,200)
        for field in ['reference','reservation_id','created_at','starts_at','ends_at']: self.assertEqual(moved[field],early[field])
        self.assertIn('t1',self.availability()[0]['available_table_ids'])
        self.assertNotIn('t4',self.availability()[0]['available_table_ids'])
        status,cancelled=request('POST','/reservations/'+early['reference']+'/cancel',{},self.tokens[0]); self.assertEqual(status,200)
        self.assertEqual(cancelled['status'],'cancelled'); self.assertIn('t4',self.availability()[0]['available_table_ids'])
        self.assertEqual(request('POST','/reservations/'+early['reference']+'/cancel',{},self.tokens[0]),(200,cancelled))
        self.err('PATCH','/reservations/'+early['reference'],{},409,'reservation_cancelled')
        self.assertEqual(len(self.listing()),2)

    def test_10_cutoff_uses_old_start(self):
        record=self.book(local='2000-02-29T18:00')
        self.err('PATCH','/reservations/'+record['reference'],{'starts_at_local':FUTURE+'T18:00','party_size':False},409,'cutoff_passed')
        self.err('POST','/reservation-moves',{'moves':[{'reference':record['reference'],'starts_at_local':FUTURE+'T18:00','table_id':'missing'}]},409,'cutoff_passed')
        self.assertEqual(self.listing(),[record])
        seed=fixture(opens='00:00',closes='23:59',duration=1,slot=1); seed['restaurants'][0]['cancellation_cutoff_minutes']=0
        now=dt.datetime.now(dt.timezone.utc).replace(second=0,microsecond=0)
        if now.hour==23 and now.minute==59: now-=dt.timedelta(minutes=1)
        self.reset(seed); self.tokens[0]=self.login()
        current=self.book(local=now.strftime('%Y-%m-%dT%H:%M'))
        self.err('POST','/reservations/'+current['reference']+'/cancel',{},409,'cutoff_passed')

    def test_11_dst_gaps_folds_absolute_duration(self):
        cases=[('Europe/Berlin','2026-03-29','2026-10-25','02:30','+02:00','03:00'),('America/New_York','2026-03-08','2026-11-01','01:30','-04:00','02:00')]
        for zone,spring,fall,fold,offset,end in cases:
            with self.subTest(zone=zone):
                self.reset(fixture(zone,opens='00:00',closes='05:00')); self.tokens[0]=self.login()
                slots=self.availability(date=spring)
                self.assertFalse(any(s['starts_at_local'][11:13]=='02' for s in slots))
                self.err('POST','/reservations',self.body(local=spring+'T02:30'),422,'invalid_local_time')
                spring_record=self.book(local=spring+'T01:30')
                self.assertEqual(spring_record['ends_at'][11:16],'04:00')
                fall_slots=self.availability(date=fall)
                matches=[s for s in fall_slots if s['starts_at_local']==fall+'T'+fold]
                self.assertEqual(len(matches),1); self.assertTrue(matches[0]['starts_at'].endswith(offset))
                record=self.book(local=fall+'T'+fold)
                self.assertTrue(record['starts_at'].endswith(offset)); self.assertEqual(record['ends_at'][11:16],end)
                self.assertEqual((dt.datetime.fromisoformat(record['ends_at'])-dt.datetime.fromisoformat(record['starts_at'])).total_seconds(),5400)
                self.err('POST','/reservations',self.body('t2',fall+'T'+fold+('-05:00' if zone.startswith('America') else '+01:00')),422,'validation_failed')
                self.assertNotIn('t1',next(s for s in self.availability(date=fall) if s['starts_at_local']==fall+'T'+fold)['available_table_ids'])

    def test_12_moves_shapes_privacy_and_cross_restaurant(self):
        a=self.book(); b=self.book('t2'); private=self.book('t3',user=1)
        status,other=request('POST','/reservations',dict(self.body('other_table'),restaurant_id='other'),self.tokens[0],'other'); self.assertEqual(status,201)
        for body in [{},{'moves':None},{'moves':{}},{'moves':[]},{'moves':[None]},{'moves':['x']},{'moves':[{}]},{'moves':[{'reference':4}]},{'moves':[{'reference':a['reference']}]*2},{'moves':[{'reference':str(i)} for i in range(9)]}]:
            with self.subTest(body=body): self.err('POST','/reservation-moves',body,422,'validation_failed')
        for ref in ['UNKNOWN',private['reference']]: self.err('POST','/reservation-moves',{'moves':[{'reference':ref}]},404,'not_found')
        self.err('POST','/reservation-moves',{'moves':[{'reference':a['reference']},{'reference':other['reference']}]},422,'validation_failed')
        for key in [None,'']: self.err('POST','/reservation-moves',{'moves':[{'reference':a['reference']}]},400,'missing_idempotency_key',key=key)
        self.err('POST','/reservation-moves',{'moves':[{'reference':a['reference']}]},422,'validation_failed',key='x'*256)
        status,no_op=request('POST','/reservation-moves',{'moves':[{'reference':b['reference'],'ignored':1},{'reference':a['reference']}]},self.tokens[0],'x'*255)
        self.assertEqual((status,no_op),(201,{'reservations':[b,a]}))

    def test_13_eight_cycle_noop_and_rollback(self):
        rows=[self.book('t'+str(i)) for i in range(8)]
        moves={'moves':[dict(reference=r['reference'],table_id='t'+str((i+1)%8)) for i,r in enumerate(rows)]}
        status,receipt=request('POST','/reservation-moves',moves,self.tokens[0],'cycle'); self.assertEqual(status,201)
        for i,updated in enumerate(receipt['reservations']):
            expected=dict(rows[i],table_id='t'+str((i+1)%8)); self.assertEqual(updated,expected)
        before=self.listing()
        no_op={'moves':[{'reference':r['reference']} for r in rows]}
        self.assertEqual(request('POST','/reservation-moves',no_op,self.tokens[0],'noop'),(201,receipt))
        bad={'moves':[dict(reference=rows[0]['reference'],table_id='t2'),dict(reference=rows[1]['reference'])]}
        self.err('POST','/reservation-moves',bad,409,'table_unavailable',key='retry')
        self.assertEqual(self.listing(),before)
        self.assertEqual(request('POST','/reservation-moves',no_op,self.tokens[0],'retry')[0],201)
        self.err('POST','/reservation-moves',{'moves':[]},409,'idempotency_key_reuse',key='cycle')

    def test_14_moves_input_order_nonoccupancy_precedence(self):
        a=self.book(); b=self.book('t2'); old=self.book('t3','2000-02-29T18:00')
        before=self.listing()
        cases=[([{'reference':a['reference'],'table_id':'t2'},{'reference':b['reference'],'party_size':False}],422,'validation_failed'),([{'reference':a['reference'],'party_size':20},{'reference':b['reference'],'table_id':'missing'}],422,'party_exceeds_capacity'),([{'reference':b['reference'],'table_id':'missing'},{'reference':a['reference'],'party_size':20}],404,'not_found'),([{'reference':old['reference'],'party_size':False},{'reference':a['reference'],'table_id':'missing'}],409,'cutoff_passed'),([{'reference':a['reference'],'party_size':False},{'reference':old['reference']}],422,'validation_failed')]
        for moves,status,code in cases:
            with self.subTest(code=code,moves=moves):
                self.err('POST','/reservation-moves',{'moves':moves},status,code)
                self.assertEqual(self.listing(),before)

    def test_15_50_identical_moves_and_original_replay(self):
        a=self.book(); b=self.book('t2')
        body={'moves':[dict(reference=a['reference'],table_id='t2'),dict(reference=b['reference'],table_id='t1')]}
        results=self.burst(lambda i:request('POST','/reservation-moves',body,self.tokens[0],'move'))
        self.assertEqual([s for s,_ in results].count(201),1); self.assertEqual([s for s,_ in results].count(200),49)
        self.assertTrue(all(v==results[0][1] for _,v in results))
        request('PATCH','/reservations/'+a['reference'],{'table_id':'t3'},self.tokens[0])
        request('POST','/reservations/'+b['reference']+'/cancel',{},self.tokens[0])
        self.assertEqual(request('POST','/reservation-moves',body,self.tokens[0],'move'),(200,results[0][1]))
        self.assertEqual(len(self.listing()),2)

    def test_16_50_amendments_single_destination(self):
        self.reset(fixture(tables=51)); self.tokens[0]=self.login()
        rows=[self.book('t'+str(i)) for i in range(50)]
        results=self.burst(lambda i:request('PATCH','/reservations/'+rows[i]['reference'],{'table_id':'t50'},self.tokens[0]))
        self.assertEqual([s for s,_ in results].count(200),1); self.assertEqual([s for s,_ in results].count(409),49)
        after=self.listing(); self.assertEqual(len({r['table_id'] for r in after}),50)
        self.assertEqual(len(after),50)

    def test_17_independent_process_snapshot_restore(self):
        self.assertNotEqual(BASE,DEST)
        extra_token=self.login()
        a=self.book(key='create-a'); b=self.book('t2',key='create-b')
        moves={'moves':[dict(reference=a['reference'],table_id='t2'),dict(reference=b['reference'],table_id='t1')]}
        status,batch=request('POST','/reservation-moves',moves,self.tokens[0],'batch'); self.assertEqual(status,201)
        request('POST','/reservations/'+a['reference']+'/cancel',{},self.tokens[0])
        self.err('POST','/reservations',dict(self.body('t4'),party_size=0),422,'validation_failed',key='failed-create')
        self.err('POST','/reservation-moves',{'moves':[]},422,'validation_failed',key='failed-batch')
        expected=self.listing(); config=request('GET','/restaurants/r')[1]
        status,snapshot=request('GET','/_test/export'); self.assertEqual(status,200)
        self.assertEqual(snapshot['track'],'tablekeeper'); self.assertEqual(snapshot['format_version'],1); self.assertIsInstance(snapshot['state'],dict)
        self.assertNotIn(PASSWORD,json.dumps(snapshot),'export must not store plaintext passwords')
        # Mutate the source after capture, without changing the snapshot held in memory.
        request('PATCH','/reservations/'+b['reference'],{'party_size':4},self.tokens[0])
        destination=fixture(); destination['users']=[dict(id='destination',email='destination@example.test',password=PASSWORD,display_name='Destination')]
        self.reset(destination,base=DEST)
        destination_token=request('POST','/auth/login',dict(email='destination@example.test',password=PASSWORD),base=DEST)[1]['token']
        for repeat in range(2):
            self.assertEqual(request('POST','/_test/import',snapshot,base=DEST)[0],204)
            self.assertEqual(self.listing(base=DEST),expected)
            self.assertEqual(self.listing(base=DEST,token=extra_token),expected)
            self.assertEqual(self.listing(base=DEST,token=self.tokens[1]),[])
            self.assertEqual(request('GET','/restaurants/r',base=DEST)[1],config)
            self.login(base=DEST)
            self.assertEqual(request('POST','/reservations',self.body(),self.tokens[0],'create-a',base=DEST),(200,a))
            self.assertEqual(request('POST','/reservation-moves',moves,self.tokens[0],'batch',base=DEST),(200,batch))
            self.err('GET','/reservations',None,401,'unauthenticated',token=destination_token,base=DEST)
            self.err('POST','/auth/login',dict(email='destination@example.test',password=PASSWORD),401,'unauthenticated',token=None,base=DEST)
        self.assertEqual(request('POST','/reservations',self.body('t4'),self.tokens[0],'failed-create',base=DEST)[0],201)
        self.assertEqual(request('POST','/reservation-moves',{'moves':[{'reference':b['reference']}]},self.tokens[0],'failed-batch',base=DEST)[0],201)
        before=self.listing(base=DEST)
        invalids=[{},dict(snapshot,track='wrong'),dict(snapshot,format_version=2),dict(snapshot,state=None),dict(snapshot,state={}),dict(snapshot,state={'nonsense':True})]
        for invalid in invalids:
            self.err('POST','/_test/import',invalid,422,'validation_failed',token=None,base=DEST)
            self.assertEqual(self.listing(base=DEST),before)
        self.err('POST','/_test/import',None,400,'malformed_request',token=None,base=DEST,raw=b'{')
        self.assertEqual(self.listing(base=DEST),before)
        self.reset(base=DEST)
        self.err('GET','/reservations',None,401,'unauthenticated',base=DEST)
        self.assertEqual(request('GET','/_test/export',base=DEST)[0],200)

    def test_18_50_logins_preserve_every_session(self):
        results=self.burst(lambda i:request('POST','/auth/login',dict(email='reviewer0@example.test',password=PASSWORD)))
        self.assertTrue(all(status==200 for status,_ in results))
        self.assertEqual(len({value['token'] for _,value in results}),50)
        for _,value in results: self.assertEqual(self.listing(token=value['token']),[])
        self.assertEqual(self.listing(),[])

    def test_19_fixture_numeric_types_and_invalid_ranges(self):
        # General field-type rules apply to fixture fields too; party_size is the
        # explicitly named exception. Every failed reset must leave service usable.
        for field in ['slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','capacity']:
            for wrong in ['30',True,[],{}]:
                seed=fixture()
                target=seed['restaurants'][0]['tables'][0] if field=='capacity' else seed['restaurants'][0]
                target[field]=wrong
                with self.subTest(field=field,wrong=wrong):
                    self.err('POST','/_test/reset',seed,400,'malformed_request',token=None)
                    self.assertEqual(self.listing(),[])
            seed=fixture()
            target=seed['restaurants'][0]['tables'][0] if field=='capacity' else seed['restaurants'][0]
            target[field]=-1
            self.err('POST','/_test/reset',seed,422,'validation_failed',token=None)
        seed=fixture();seed['users'][0]['id']='u'*65
        self.err('POST','/_test/reset',seed,422,'validation_failed',token=None)

    def test_20_dst_closing_and_grid_from_offset_open(self):
        for zone,date,offset in [('Europe/Berlin','2026-10-25','+02:00'),('America/New_York','2026-11-01','-04:00')]:
            with self.subTest(zone=zone):
                seed=fixture(zone,opens='00:15',closes='04:15',duration=90,slot=30)
                self.reset(seed);self.tokens[0]=self.login()
                date_value=dt.date.fromisoformat(date); zone_value=ZoneInfo(zone)
                closing=dt.datetime.combine(date_value,dt.time(4,15),zone_value).astimezone(dt.timezone.utc)
                expected=[]
                for minute in range(15,255,30):
                    wall=dt.datetime.combine(date_value,dt.time(minute//60,minute%60))
                    start=wall.replace(tzinfo=zone_value,fold=0)
                    if start.astimezone(dt.timezone.utc)+dt.timedelta(minutes=90)<=closing:
                        expected.append(wall.isoformat(timespec='minutes'))
                self.assertEqual([s['starts_at_local'] for s in self.availability(date)],expected)
                record=self.book(local=expected[-1])
                actual_end=dt.datetime.fromisoformat(record['ends_at']).astimezone(dt.timezone.utc)
                self.assertLessEqual(actual_end,closing)
                self.assertEqual(actual_end-dt.datetime.fromisoformat(record['starts_at']).astimezone(dt.timezone.utc),dt.timedelta(minutes=90))
                self.err('POST','/reservations',self.body('t2',date+'T03:15'),422,'outside_opening_hours')

    def test_21_deep_ignored_body_is_atomic_and_replayable(self):
        # Independently reproduce planner's concrete unknown-field/atomicity probe.
        nested=0
        for _ in range(600): nested=[nested]
        body=dict(self.body(),ignored=nested)
        status,receipt=request('POST','/reservations',body,self.tokens[0],'deep')
        after=self.listing()
        self.assertEqual((status,len(after)),(201,1),
                         'valid ignored field must succeed; any rejection must not persist a booking')
        self.assertEqual(request('POST','/reservations',body,self.tokens[0],'deep'),(200,receipt))
        batch={'moves':[{'reference':receipt['reference'],'table_id':'t2'}],'ignored':nested}
        status,response=request('POST','/reservation-moves',batch,self.tokens[0],'deep-batch')
        self.assertEqual(status,201)
        self.assertEqual(request('POST','/reservation-moves',batch,self.tokens[0],'deep-batch'),(200,response))
        status,snapshot=request('GET','/_test/export');self.assertEqual(status,200)
        self.assertEqual(request('POST','/_test/import',snapshot,base=DEST)[0],204)
        self.assertEqual(request('POST','/reservations',body,self.tokens[0],'deep',base=DEST),(200,receipt))

    def test_22_same_body_cross_path_and_numeric_equality(self):
        original=self.book('t3')
        hybrid=dict(self.body(),moves=[{'reference':original['reference'],'table_id':'t4'}],ignored=1)
        status,created=request('POST','/reservations',hybrid,self.tokens[0],'both');self.assertEqual(status,201)
        status,batch=request('POST','/reservation-moves',hybrid,self.tokens[0],'both');self.assertEqual(status,201)
        numeric=dict(hybrid,party_size=2.0,ignored=1.0)
        self.assertEqual(request('POST','/reservations',numeric,self.tokens[0],'both'),(200,created))
        self.assertEqual(request('POST','/reservation-moves',numeric,self.tokens[0],'both'),(200,batch))
        status,_=request('PATCH','/reservations/'+created['reference'],{'party_size':3},self.tokens[0],'both');self.assertEqual(status,200)
        self.assertEqual(request('POST','/reservations',hybrid,self.tokens[0],'both'),(200,created))

    def test_23_concurrent_atomic_export_and_moves(self):
        a=self.book();b=self.book('t2')
        def action(i):
            if i%2:return request('GET','/_test/export')
            tables=['t1','t2'] if i%4 else ['t2','t1']
            body={'moves':[{'reference':r['reference'],'table_id':t} for r,t in zip([a,b],tables)]}
            return request('POST','/reservation-moves',body,self.tokens[0],'atomic-'+str(i))
        results=self.burst(action)
        for i,(status,value) in enumerate(results):
            self.assertEqual(status,200 if i%2 else 201)
            if i%2:
                self.assertEqual(request('POST','/_test/import',value,base=DEST)[0],204)
                rows=self.listing(base=DEST)
                self.assertEqual(len(rows),2)
                self.assertEqual({r['table_id'] for r in rows},{'t1','t2'})
                self.assertEqual({r['reference'] for r in rows},{a['reference'],b['reference']})

    def test_24_deep_moves_commit_and_receipt_together(self):
        a=self.book()
        nested=0
        for _ in range(600):nested=[nested]
        body={'moves':[{'reference':a['reference'],'table_id':'t2'}],'ignored':nested}
        status,response=request('POST','/reservation-moves',body,self.tokens[0],'deep-move-alone')
        after=self.listing()
        self.assertEqual((status,after[0]['table_id']),(201,'t2'),
                         'valid ignored field must succeed; rejected batch must retain original table t1')
        self.assertEqual(request('POST','/reservation-moves',body,self.tokens[0],'deep-move-alone'),(200,response))

    def test_25_table_ids_are_scoped_by_restaurant(self):
        # Regression derived from actual official failure: two restaurant-local
        # table catalogues can reuse IDs; occupancy must include restaurant ID.
        seed=fixture();seed['restaurants'][1]['tables']=copy.deepcopy(seed['restaurants'][0]['tables'])
        self.reset(seed);self.tokens[0]=self.login()
        first=self.book()
        status,second=request('POST','/reservations',dict(self.body(),restaurant_id='other'),self.tokens[0],'other-same-table')
        self.assertEqual(status,201)
        self.assertNotEqual(first['reference'],second['reference'])
        self.assertNotIn('t1',self.availability()[0]['available_table_ids'])
        request('POST','/reservations/'+first['reference']+'/cancel',{},self.tokens[0])
        self.assertIn('t1',self.availability()[0]['available_table_ids'])
        status,other=request('GET','/availability?'+urllib.parse.urlencode(dict(restaurant_id='other',date=FUTURE,party_size=2)))
        self.assertEqual(status,200);self.assertNotIn('t1',other['slots'][0]['available_table_ids'])
        snapshot=request('GET','/_test/export')[1]
        self.assertEqual(request('POST','/_test/import',snapshot,base=DEST)[0],204)
        self.assertEqual(self.listing(base=DEST),self.listing())

    def test_26_opaque_restaurant_ids_remain_publicly_addressable(self):
        # Planner's candidate, independently exercised on the next frozen commit.
        # A percent-encoded slash belongs to the opaque ID, not the route grammar.
        for rid in ['branch/one','分店/一','literal%2Fname']:
            with self.subTest(restaurant_id=rid):
                seed=fixture();seed['restaurants'][0]['id']=rid
                self.reset(seed)
                self.assertEqual(request('GET','/restaurants')[1]['restaurants'][0]['id'],rid)
                path='/restaurants/'+urllib.parse.quote(rid,safe='')
                self.assertEqual(request('GET',path),(200,seed['restaurants'][0]))
                self.err('GET','/restaurants/'+urllib.parse.quote(rid+'/missing',safe=''),None,404,'not_found',token=None)
                status,availability=request('GET','/availability?'+urllib.parse.urlencode(dict(restaurant_id=rid,date=FUTURE,party_size=2)))
                self.assertEqual(status,200);self.assertEqual(availability['restaurant_id'],rid)
                self.tokens[0]=self.login()
                status,record=request('POST','/reservations',dict(self.body(),restaurant_id=rid),self.tokens[0],'opaque')
                self.assertEqual(status,201);self.assertEqual(record['restaurant_id'],rid)

    def test_27_deep_decoder_syntax_retry_and_portable_receipts(self):
        # Exercise the new explicit-stack decoder through HTTP only; independent
        # input construction uses string operations, not service JSON helpers.
        prefix=json.dumps(self.body())[:-1]+',"ignored":'
        def raw(center='{"flag":true,"text":"a\\\\b\\\"c","n":1}',depth=1100):
            return (prefix+'['*depth+center+']'*depth+'}').encode()
        valid=raw()
        status,receipt=request('POST','/reservations',token=self.tokens[0],key='deep1100',raw=valid)
        self.assertEqual(status,201)
        self.assertEqual(request('POST','/reservations',token=self.tokens[0],key='deep1100',raw=valid),(200,receipt))
        self.err('POST','/reservations',None,409,'idempotency_key_reuse',key='deep1100',raw=raw('{"flag":1,"text":"a\\\\b\\\"c","n":1}'))
        before=self.listing()
        for center in ['{"a":1,}','[1,]','{"a" 1}','{"a":NaN}','{"a":true false}','01','{"a":"unterminated}']:
            with self.subTest(center=center):
                self.err('POST','/reservations',None,400,'malformed_request',key='malformed-deep',raw=raw(center))
                self.assertEqual(self.listing(),before)
        # Failed parse consumes no receipt.
        self.assertEqual(request('POST','/reservations',self.body('t2'),self.tokens[0],'malformed-deep')[0],201)
        _,snapshot=request('GET','/_test/export',parse_json=False)
        self.assertEqual(request('POST','/_test/import',raw=snapshot,base=DEST)[0],204)
        self.assertEqual(request('POST','/reservations',token=self.tokens[0],key='deep1100',raw=valid,base=DEST),(200,receipt))


if __name__ == '__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        ordinary=[t for _,p,_,t in METRICS if not p.startswith('/_test/')]
        controls=[t for _,p,_,t in METRICS if p.startswith('/_test/')]
        print(json.dumps(dict(http_requests=len(METRICS),normal_max_seconds=max(ordinary,default=0),
                              test_control_max_seconds=max(controls,default=0),
                              observed_5xx=sum(s>=500 for _,_,s,_ in METRICS)),sort_keys=True))
