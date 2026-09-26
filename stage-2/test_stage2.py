"""Focused Stage 2 HTTP/browser checks. External URLs supplied by the evidence runner."""
import copy
import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright, expect
import test_contract as base


def fixture():
    data = base.fixture()
    r = data['restaurants'][0]
    r['name'] = 'The Fern Room'
    r['combinable'] = [['t2', 't1'], ['t2', 't3']]
    for table, label in zip(r['tables'], ['Window table', 'Garden booth', 'Corner table', 'Long table']):
        table['label'] = label
    return data


class Stage2(unittest.TestCase):
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

    def pair(self, **extra):
        body = self.booking(**extra)
        body.pop('table_id', None)
        body.setdefault('table_ids', ['t1', 't2'])
        return body

    def test_combinations_order_capacity_overlap_and_cancel(self):
        data = self.request('GET', '/availability?restaurant_id=r&date=2032-10-25&party_size=5')[1]
        slot = data['slots'][0]
        self.assertEqual(slot['available_table_ids'], ['t3', 't4'])
        self.assertEqual([o['table_ids'] for o in slot['available_options']], [['t3'], ['t4'], ['t2', 't1'], ['t2', 't3']])
        status, record = self.request('POST', '/reservations', self.pair(party_size=6), self.ada, 'pair')
        self.assertEqual(status, 201)
        self.assertEqual(record['table_ids'], ['t2', 't1'])
        self.assertNotIn('table_id', record)
        for table in ['t1', 't2']:
            self.error(self.request('POST', '/reservations', self.booking(table_id=table), self.bob, table), 409, 'table_unavailable')
        self.assertEqual(self.request('POST', '/reservations/' + record['reference'] + '/cancel', {}, self.ada)[0], 200)
        self.assertEqual(self.request('POST', '/reservations', self.pair(party_size=6), self.ada, 'pair'), (200, record))
        self.create('free')

    def test_combination_validation_amend_moves_seed_and_import(self):
        for body, code, status in [
            (self.pair(table_ids=['t1','t3']), 'combination_not_allowed', 422),
            (self.pair(table_ids=['t1','t2','t3']), 'combination_not_allowed', 422),
            (self.pair(table_ids=['t1','t1']), 'validation_failed', 422),
            (self.pair(table_ids=[]), 'validation_failed', 422),
            (self.pair(table_ids=['t1','missing']), 'not_found', 404),
            (self.pair(table_ids='t1'), 'malformed_request', 400),
            ({**self.pair(), 'table_id':'t1'}, 'validation_failed', 422),
            (self.pair(party_size=7), 'party_exceeds_capacity', 422)]:
            self.error(self.request('POST', '/reservations', body, self.ada, 'failed'), status, code)
        a, b = self.create('a'), self.create('b',table_id='t3')
        moves = {'moves':[{'reference':a['reference'],'table_ids':['t3','t2']}, {'reference':b['reference'],'table_id':'t1'}]}
        moved = self.request('POST', '/reservation-moves', moves, self.ada, 'failed')
        self.assertEqual(moved[0], 201)
        self.assertEqual(moved[1]['reservations'][0]['table_ids'], ['t2','t3'])
        self.assertNotIn('table_id', moved[1]['reservations'][0])
        self.assertEqual(self.request('PATCH', '/reservations/'+a['reference'], {'table_id':'t2'}, self.ada)[0], 200)
        snapshot = self.snapshot()
        self.assertEqual(self.request('POST', '/_test/import', snapshot, server=1)[0], 204)
        self.assertTrue(snapshot == self.snapshot(server=1))
        self.assertEqual(self.request('POST', '/reservation-moves', moves, self.ada, 'failed', server=1), (200,moved[1]))
        seed = fixture()
        seed['reservations'] = [{**self.pair(), 'id':'seed', 'reference':'CANCEL01', 'user_id':'ada', 'status':'cancelled'}]
        self.assertEqual(self.request('POST', '/_test/reset', seed)[0], 204)
        self.ada = self.login('ada')
        self.create('cancelled-frees-all')

    def test_50_pair_and_single_contention(self):
        with ThreadPoolExecutor(max_workers=50) as pool:
            result = list(pool.map(lambda n:self.request('POST','/reservations',self.pair() if n%2 else self.booking(),self.ada,str(n)),range(50)))
        self.assertEqual(sum(status == 201 for status,_ in result), 1)
        self.assertEqual(sum(status == 409 for status,_ in result), 49)

    def browser(self):
        p = sync_playwright().start()
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width':1440,'height':1000})
        self.addCleanup(p.stop)
        self.addCleanup(browser.close)
        return context.new_page()

    def sign_in(self, page):
        page.goto(self.urls[0]+'/login')
        page.get_by_test_id('login-email').fill('ada@example.test')
        page.get_by_test_id('login-password').fill('fixture-pass')
        page.get_by_test_id('login-submit').click()
        expect(page.get_by_test_id('current-user')).to_contain_text('Ada')
        expect(page.get_by_test_id('restaurant-select')).to_have_value('r')

    def search(self, page, party=2, date='2032-10-25'):
        page.get_by_test_id('date-input').fill(date)
        page.get_by_test_id('party-size-input').fill(str(party))
        page.get_by_test_id('search-button').click()
        expect(page.get_by_test_id('availability-grid')).to_be_visible()

    def test_browser_pair_uncertainty_retry_and_375px(self):
        page = self.browser(); self.sign_in(page); self.search(page, 5)
        page.get_by_test_id('slot-t2+t1-19:00').click()
        expect(page.get_by_test_id('booking-summary')).to_contain_text('Garden booth + Window table')
        captured = []
        def lost(route):
            response = route.fetch()
            captured.append((route.request.headers.get('idempotency-key'), response.json()['reference']))
            route.abort('failed')
        page.route('**/reservations', lost)
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('booking-uncertain')).to_be_visible()
        expect(page.get_by_test_id('booking-error')).to_have_count(0)
        expect(page.get_by_test_id('confirmation')).to_have_count(0)
        page.unroute('**/reservations', lost)
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('confirmation-reference')).to_have_text(captured[0][1])
        expect(page.get_by_test_id('booking-uncertain')).to_have_count(0)
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('confirmation-reference')).to_have_text(captured[0][1])
        records = self.request('GET','/reservations',token=self.ada)[1]['reservations']
        self.assertEqual(len(records),1)
        out = Path(os.environ['BUILDER_EVIDENCE'])
        page.screenshot(path=str(out/'desktop-confirmation.png'),full_page=True)
        page.set_viewport_size({'width':375,'height':900})
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        page.screenshot(path=str(out/'mobile-confirmation.png'),full_page=True)
        page.goto(self.urls[0]+'/lookup')
        expect(page.get_by_test_id('current-user')).to_contain_text('Ada')
        page.get_by_test_id('lookup-reference-input').fill(captured[0][1]); page.get_by_test_id('lookup-submit').click()
        expect(page.get_by_test_id('reservation-tables')).to_contain_text('Garden booth + Window table')
        page.get_by_test_id('reservation-cancel-button').click()
        expect(page.get_by_test_id('reservation-status')).to_have_text('cancelled')
        expect(page.get_by_test_id('reservation-cancel-button')).to_have_count(0)

    def test_browser_stale_choice_preserves_form_and_refreshes(self):
        page = self.browser(); self.sign_in(page); self.search(page)
        page.get_by_test_id('slot-t1-19:00').click()
        self.assertEqual(self.request('POST','/reservations',self.booking(),self.bob,'competing')[0],201)
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('booking-error')).to_be_visible()
        expect(page.get_by_test_id('slot-t1-19:00')).to_have_attribute('data-available','false')
        expect(page.get_by_test_id('booking-form')).to_be_visible()
        expect(page.get_by_test_id('booking-party-size')).to_have_value('2')
        expect(page.get_by_test_id('confirmation')).to_have_count(0)

    def test_browser_long_names_wrap_in_all_booking_states(self):
        seed = fixture()
        name = 'Restaurantwithanexceptionallylongsinglewordname'
        label = 'Windowtablewithanexceptionallylongsinglewordlabel'
        seed['restaurants'][0]['name'] = name
        seed['restaurants'][0]['tables'][0]['label'] = label
        # Tuesday is closed, allowing the same valid text through the empty state.
        seed['restaurants'][0]['opening_hours'] = [h for h in seed['restaurants'][0]['opening_hours'] if h['weekday'] != 'tue']
        self.assertEqual(self.request('POST', '/_test/reset', seed)[0], 204)
        page = self.browser(); page.set_viewport_size({'width':375,'height':812})
        self.sign_in(page); self.search(page)
        def contained():
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),375)
        expect(page.locator('#results h2')).to_have_text(name); contained()
        page.get_by_test_id('slot-t1-19:00').click(); contained()
        expect(page.get_by_test_id('booking-summary')).to_contain_text(label)
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('confirmation')).to_be_visible(); contained()
        reference = page.get_by_test_id('confirmation-reference').inner_text()
        page.screenshot(path=str(Path(os.environ['BUILDER_EVIDENCE'])/'mobile-long-name-confirmation.png'),full_page=True)
        page.goto(self.urls[0]+'/lookup?reference='+reference)
        expect(page.get_by_test_id('reservation-status')).to_have_text('confirmed'); contained()
        expect(page.get_by_test_id('reservation-tables')).to_have_text(label)
        page.screenshot(path=str(Path(os.environ['BUILDER_EVIDENCE'])/'mobile-long-name-lookup.png'),full_page=True)
        page.goto(self.urls[0]+'/')
        expect(page.get_by_test_id('restaurant-select')).to_have_value('r')
        page.get_by_test_id('date-input').fill('2032-10-26')
        page.get_by_test_id('search-button').click()
        expect(page.get_by_test_id('no-slots')).to_contain_text(name); contained()

    def test_browser_late_search_cannot_restore_old_restaurant_or_form(self):
        seed=fixture(); other=copy.deepcopy(seed['restaurants'][0]); other['id']='b'; other['name']='The Courtyard'; other['tables'][0]['label']='Courtyard bench'; seed['restaurants'].append(other)
        self.request('POST','/_test/reset',seed)
        page=self.browser(); self.sign_in(page)
        delayed=[]
        def hold(route):
            if parse_qs(urlsplit(route.request.url).query).get('restaurant_id') == ['r']:
                delayed.append(route)
            else: route.continue_()
        page.route('**/availability?*',hold)
        page.get_by_test_id('date-input').fill('2032-10-25'); page.get_by_test_id('search-button').click()
        page.get_by_test_id('restaurant-select').select_option('b'); page.get_by_test_id('search-button').click()
        expect(page.locator('#results h2')).to_have_text('The Courtyard')
        page.get_by_test_id('slot-t1-19:00').click()
        old=self.request('GET','/availability?restaurant_id=r&date=2032-10-25&party_size=2')[1]
        for route in delayed: route.fulfill(status=200,content_type='application/json',body=json.dumps(old))
        page.wait_for_timeout(80)
        expect(page.locator('#results h2')).to_have_text('The Courtyard')
        expect(page.get_by_test_id('booking-summary')).to_contain_text('Courtyard bench')

    def test_browser_stage1_upgrade_retains_session_form_and_original_receipt(self):
        legacy=os.environ['TABLEKEEPER_STAGE1_URL']
        with urlopen(Request(legacy+'/_test/reset',data=json.dumps(base.fixture()).encode(),headers={'Content-Type':'application/json'},method='POST')) as response:
            self.assertEqual(response.status,204)
        page=self.browser(); captured=[]
        def old_service(route):
            parsed=urlsplit(route.request.url)
            response=route.fetch(url=legacy+parsed.path+('?' + parsed.query if parsed.query else ''))
            if parsed.path == '/reservations' and route.request.method == 'POST':
                captured.append(response.json()['reference']); route.abort('failed')
            else: route.fulfill(response=response)
        for pattern in ['**/auth/**','**/restaurants**','**/availability?*','**/reservations**']: page.route(pattern,old_service)
        self.sign_in(page); self.search(page); page.get_by_test_id('slot-t1-19:00').click(); page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('booking-uncertain')).to_be_visible()
        with urlopen(legacy+'/_test/export') as response: snapshot=response.read()
        self.assertEqual(self.request('POST','/_test/import',raw=snapshot)[0],204)
        page.unroute_all()
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('confirmation-reference')).to_have_text(captured[0])
        expect(page.get_by_test_id('current-user')).to_contain_text('Ada')
        page.goto(self.urls[0]+'/lookup?reference='+captured[0]); expect(page.get_by_test_id('reservation-status')).to_have_text('confirmed')


if __name__ == '__main__': unittest.main(verbosity=2)
