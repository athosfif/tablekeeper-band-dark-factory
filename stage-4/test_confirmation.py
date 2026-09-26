"""Rendered confirmation checks against a running container, including read races."""
import json
import os
from pathlib import Path
import unittest

from playwright.sync_api import expect, sync_playwright
from test_stage2 import Stage2
from test_stage4 import Stage4


class Confirmation(unittest.TestCase):
    setUpClass = Stage4.__dict__['setUpClass']
    tearDownClass = Stage4.__dict__['tearDownClass']
    setUp = Stage4.setUp
    request = Stage4.request
    login = Stage4.login
    closure = Stage4.closure
    preview = Stage4.preview
    apply = Stage4.apply
    sign_in = Stage2.sign_in
    search = Stage2.search

    def browser(self):
        if not hasattr(self,'running_browser'):
            playwright = sync_playwright().start()
            self.running_browser = playwright.chromium.launch()
            self.addCleanup(playwright.stop)
            self.addCleanup(self.running_browser.close)
        return self.running_browser.new_page(viewport={'width':375,'height':900})

    def open_form(self, pair=False):
        page = self.browser()
        page.set_viewport_size({'width':375, 'height':900})
        self.sign_in(page); self.search(page, 5 if pair else 2)
        page.get_by_test_id('slot-t2+t1-19:00' if pair else 'slot-t1-19:00').click()
        return page

    def capture_posts(self, page, lose=False):
        captured = []
        def intercept(route):
            response = route.fetch()
            captured.append((route.request.headers['idempotency-key'], route.request.post_data_json, response.status, response.json()))
            if lose: route.abort('failed')
            else: route.fulfill(response=response)
        page.route('**/reservations', intercept)
        return captured, intercept

    def submit(self, page):
        with page.expect_response(lambda r:r.request.method == 'POST' and r.url.endswith('/reservations')) as pending:
            page.get_by_test_id('booking-submit').click()
        return pending.value.json()

    def move(self, reference):
        result = self.apply(self.preview())
        self.assertEqual(result[0],201)
        return next(r for r in result[1]['reservations'] if r['reference'] == reference)

    def assert_current(self, page, record):
        restaurant = self.request('GET','/restaurants/r')[1]
        names = [next(t['label'] for t in restaurant['tables'] if t['id'] == tid) for tid in record['table_ids']]
        expect(page.get_by_test_id('confirmation-reference')).to_have_text(record['reference'])
        expect(page.get_by_test_id('confirmation-tables')).to_have_text(' + '.join(names))
        for name in names: expect(page.get_by_test_id('confirmation-details')).to_contain_text(name)
        expect(page.get_by_test_id('booking-error')).to_have_count(0)
        expect(page.get_by_test_id('booking-uncertain')).to_have_count(0)
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),page.viewport_size['width'])

    def test_original_single_and_pair_receipts_display_current_seating(self):
        for pair in (False,True):
            with self.subTest(pair=pair):
                self.setUp()
                page=self.open_form(pair); posts,_=self.capture_posts(page)
                receipt=self.submit(page); self.assert_current(page,receipt)
                moved=self.move(receipt['reference'])
                self.assertNotEqual(receipt['table_ids'],moved['table_ids'])
                self.assertEqual(self.submit(page),receipt)
                self.assert_current(page,moved)
                self.assertEqual(posts[0][:2],posts[1][:2]); self.assertEqual([p[2] for p in posts],[201,200])
                self.assertEqual(len(self.request('GET','/reservations',token=self.ada)[1]['reservations']),1)
                for width in (375,1440):
                    page.set_viewport_size({'width':width,'height':900})
                    self.assert_current(page,moved)
                    page.screenshot(path=str(Path(os.environ['BUILDER_EVIDENCE'])/f'current-confirmation-{pair}-{width}.png'),full_page=True)
                page.close()

    def test_failed_details_keep_known_success_and_retry_only_the_read(self):
        for failure in ('network','http'):
            with self.subTest(failure=failure):
                self.setUp(); page=self.open_form(); posts,_=self.capture_posts(page)
                def unavailable(route):
                    if failure == 'network': route.abort('failed')
                    else: route.fulfill(status=503,content_type='application/json',body=json.dumps({'error':{'message':'Unavailable'}}))
                page.route('**/reservations/*',unavailable)
                receipt=self.submit(page)
                expect(page.get_by_test_id('confirmation-refresh-error')).to_contain_text('booking response was successful')
                expect(page.get_by_test_id('confirmation-reference')).to_have_text(receipt['reference'])
                expect(page.get_by_test_id('confirmation-tables')).to_have_count(0)
                expect(page.get_by_test_id('booking-error')).to_have_count(0)
                expect(page.get_by_test_id('booking-uncertain')).to_have_count(0)
                page.screenshot(path=str(Path(os.environ['BUILDER_EVIDENCE'])/f'details-unavailable-{failure}.png'),full_page=True)
                moved=self.move(receipt['reference'])
                page.unroute('**/reservations/*',unavailable)
                page.get_by_test_id('confirmation-refresh-button').click()
                self.assert_current(page,moved)
                expect(page.get_by_test_id('confirmation-refresh-error')).to_have_count(0)
                self.assertEqual(len(posts),1)
                self.assertEqual(self.submit(page),receipt); self.assert_current(page,moved)
                self.assertEqual(posts[0][:2],posts[1][:2]); page.close()

    def test_late_detail_success_or_failure_cannot_replace_new_selection(self):
        for failure in (False,True):
            with self.subTest(failure=failure):
                self.setUp(); page=self.open_form(); held=[]
                page.route('**/reservations/*',lambda route:held.append(route))
                receipt=self.submit(page)
                expect(page.locator('#confirmation-refresh')).to_contain_text('Checking current seating')
                page.get_by_test_id('slot-t4-20:30').click()
                expect(page.get_by_test_id('booking-summary')).to_contain_text('Long table')
                self.assertEqual(len(held),1)
                with page.expect_response(lambda r:r.url.endswith('/'+receipt['reference'])):
                    held[0].fulfill(status=404 if failure else 200,content_type='application/json',body=json.dumps({'error':{'message':'Not found'}} if failure else receipt))
                # Let the fetch continuation run; the new form must stay untouched.
                page.wait_for_timeout(80)
                expect(page.get_by_test_id('confirmation')).to_have_count(0)
                expect(page.get_by_test_id('confirmation-refresh-error')).to_have_count(0)
                expect(page.get_by_test_id('booking-summary')).to_contain_text('Long table')
                page.unroute_all()
                new=self.submit(page); self.assert_current(page,new)
                self.assertNotEqual(new['reference'],receipt['reference']); page.close()

    def test_lost_post_then_replan_recovers_original_reference_and_current_seating(self):
        page=self.open_form(True); posts,intercept=self.capture_posts(page,lose=True)
        page.get_by_test_id('booking-submit').click()
        expect(page.get_by_test_id('booking-uncertain')).to_be_visible()
        expect(page.get_by_test_id('confirmation')).to_have_count(0)
        original=posts[0][3]; moved=self.move(original['reference'])
        page.unroute('**/reservations',intercept)
        retried,_=self.capture_posts(page)
        self.assertEqual(self.submit(page),original); self.assert_current(page,moved)
        self.assertEqual(posts[0][:2],retried[0][:2]); self.assertEqual(retried[0][2],200)
        self.assertEqual(len(self.request('GET','/reservations',token=self.ada)[1]['reservations']),1)


if __name__ == '__main__': unittest.main(verbosity=2)
