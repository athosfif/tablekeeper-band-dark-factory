"""Real-browser Stage2 contracts. No implementation imports or saved sessions."""
import asyncio
import base64
import json
import os
import unittest
from urllib.parse import urlsplit, parse_qs
from playwright.async_api import async_playwright, expect
import reviewer_inherited as api
from reviewer_pair_checks import pair_fixture, DAY, OLD

BASE=api.BASE
DEST=api.DEST

class BrowserChecks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.seed=pair_fixture()
        self.seed['restaurants'][1]['name']='Harbour Room'
        api.request('POST','/_test/reset',self.seed)
        self.token=api.request('POST','/auth/login',{'email':'reviewer0@example.test','password':api.PASSWORD})[1]['token']
        self.pw=await async_playwright().start()
        self.browser=await self.pw.chromium.launch(headless=True,args=['--no-sandbox'])
        self.context=await self.browser.new_context(viewport={'width':1280,'height':900})
        self.page=await self.context.new_page()
        self.page.set_default_timeout(7000)
        self.external=[]
        async def local_only(route):
            if urlsplit(route.request.url).netloc != urlsplit(BASE).netloc:
                self.external.append(urlsplit(route.request.url).netloc)
                await route.abort()
            else: await route.continue_()
        await self.context.route('**/*',local_only)

    async def asyncTearDown(self):
        await self.browser.close();await self.pw.stop()
        self.assertEqual(self.external,[], 'Runtime requested external assets')

    def el(self,name):return self.page.get_by_test_id(name)

    async def shot(self,name):
        data=await self.page.screenshot(full_page=True)
        print('REVIEW_SCREENSHOT '+name+' '+base64.b64encode(data).decode(),flush=True)

    async def sign_in(self):
        await self.page.goto(BASE+'/login')
        await self.el('login-email').fill('reviewer0@example.test')
        await self.el('login-password').fill(api.PASSWORD)
        async with self.page.expect_response(lambda r:urlsplit(r.url).path=='/auth/login' and r.request.method=='POST') as response:
            await self.el('login-submit').click()
        self.assertEqual((await response.value).status,200)
        await self.page.wait_for_url(BASE+'/')
        await expect(self.el('current-user')).to_contain_text('Reviewer 0')

    async def search(self,party=4,restaurant='r',day=DAY):
        if urlsplit(self.page.url).path!='/':await self.page.goto(BASE+'/')
        await self.el('restaurant-select').select_option(restaurant)
        await self.el('date-input').fill(day)
        await self.el('party-size-input').fill(str(party))
        await self.el('search-button').click()
        await expect(self.el('availability-grid')).to_be_visible()

    async def choose(self,pair=False):
        await self.search()
        await self.el('slot-b+a-18:00' if pair else 'slot-c-18:00').click()
        await expect(self.el('booking-form')).to_be_visible()
        await expect(self.el('booking-party-size')).to_have_value('4')
        await expect(self.el('booking-summary')).to_contain_text('18:00')
        for name in (['Courtyard','Window nook'] if pair else ['Garden alcove']):
            await expect(self.el('booking-summary')).to_contain_text(name)

    async def assert_feedback(self,kind):
        await expect(self.el(kind)).to_be_visible()
        self.assertTrue((await self.el(kind).inner_text()).strip())
        other='booking-error' if kind=='booking-uncertain' else 'booking-uncertain'
        await expect(self.el(other)).to_have_count(0)
        await expect(self.el('confirmation')).to_have_count(0)

    async def test_browser_01_routes_auth_and_logout(self):
        for path in ['/','/signup','/login','/lookup']:
            response=await self.page.goto(BASE+path)
            self.assertEqual(response.status,200)
            self.assertIn('text/html',response.headers.get('content-type',''))
        await self.page.goto(BASE+'/login')
        await self.el('login-email').fill('nobody@example.test')
        await self.el('login-password').fill('synthetic wrong password')
        await self.el('login-submit').click();await expect(self.el('auth-error')).to_be_visible()
        await self.sign_in()
        for path in ['/','/signup','/login','/lookup']:
            await self.page.goto(BASE+path)
            await expect(self.el('current-user')).to_contain_text('Reviewer 0')
            await expect(self.el('logout-button')).to_be_visible()
        await self.el('logout-button').click();await expect(self.el('current-user')).to_have_count(0)
        await self.search()
        await self.el('slot-c-18:00').click()
        await self.page.wait_for_function("location.pathname==='/login'||!!document.querySelector('[data-testid=auth-error]')")

    async def test_browser_02_grid_mobile_labels_and_empty(self):
        await self.sign_in();await self.search()
        slots=api.request('GET','/availability?restaurant_id=r&date='+DAY+'&party_size=4')[1]['slots']
        for slot in slots:
            clock=slot['starts_at_local'][-5:]
            for table in self.seed['restaurants'][0]['tables']:
                cell=self.el('slot-'+table['id']+'-'+clock)
                await expect(cell).to_have_count(1)
                await expect(cell).to_have_attribute('data-available','true' if table['id'] in slot['available_table_ids'] else 'false')
        # Use real pointer input: synthetic dispatch bypasses native disabled behavior.
        unavailable=await self.el('slot-a-18:00').bounding_box()
        await self.page.mouse.click(unavailable['x']+unavailable['width']/2,unavailable['y']+unavailable['height']/2)
        await expect(self.el('booking-form')).to_have_count(0)
        await self.shot('desktop-grid')
        await self.page.set_viewport_size({'width':375,'height':812})
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        for field in ['restaurant-select','date-input','party-size-input']:
            self.assertTrue(await self.el(field).evaluate("e=>!!(e.labels&&[...e.labels].some(l=>l.textContent.trim()))"))
        await self.el('search-button').focus()
        self.assertTrue(await self.el('search-button').evaluate('e=>document.activeElement===e'))
        await self.shot('mobile-grid-focus')
        self.seed['restaurants'][0]['opening_hours']=[];api.request('POST','/_test/reset',self.seed)
        await self.el('search-button').click();await expect(self.el('no-slots')).to_be_visible()
        await expect(self.el('availability-grid')).to_have_count(0)
        await self.shot('mobile-empty')

    async def test_browser_03_single_pair_success_replay_lookup(self):
        for pair in [False,True]:
            with self.subTest(pair=pair):
                api.request('POST','/_test/reset',self.seed);await self.sign_in();await self.choose(pair)
                requests=[]
                async def observe(route):
                    requests.append((route.request.post_data,route.request.headers.get('idempotency-key')))
                    await route.continue_()
                await self.page.route('**/reservations',observe)
                await self.el('booking-submit').click();await expect(self.el('confirmation')).to_be_visible()
                ref=(await self.el('confirmation-reference').inner_text()).strip()
                self.assertRegex(ref,r'^[A-Z0-9]{6,12}$')
                self.assertEqual(await self.el('confirmation-reference').inner_text(),ref)
                await expect(self.el('booking-form')).to_be_visible()
                for label in ['Review café','18:00']+(['Courtyard','Window nook'] if pair else ['Garden alcove']):
                    await expect(self.el('confirmation-details')).to_contain_text(label)
                for label in (['Courtyard','Window nook'] if pair else ['Garden alcove']):
                    await expect(self.el('confirmation-tables')).to_contain_text(label)
                await self.shot('pair-confirmed' if pair else 'single-confirmed')
                async with self.page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST'):
                    await self.el('booking-submit').click()
                await expect(self.el('confirmation-reference')).to_have_text(ref)
                self.assertGreaterEqual(len(requests),2);self.assertEqual(requests[-1],requests[-2]);self.assertTrue(requests[-1][1])
                await self.el('booking-party-size').fill('3');await self.el('booking-submit').click()
                await expect(self.el('booking-error')).to_be_visible()
                self.assertNotEqual(requests[-1][1],requests[-2][1])
                await self.page.unroute('**/reservations',observe)
                await self.page.goto(BASE+'/lookup')
                await self.el('lookup-reference-input').fill(ref);await self.el('lookup-submit').click()
                await expect(self.el('reservation-status')).to_have_text('confirmed')
                for label in (['Courtyard','Window nook'] if pair else ['Garden alcove']):
                    await expect(self.el('reservation-tables')).to_contain_text(label)
                await self.el('reservation-cancel-button').click();await expect(self.el('reservation-status')).to_have_text('cancelled')
                await expect(self.el('reservation-cancel-button')).to_have_count(0)
                await self.shot('pair-cancelled' if pair else 'single-cancelled')

    async def test_browser_04_stale_selection_preserves_form(self):
        for pair in [False,True]:
            api.request('POST','/_test/reset',self.seed);await self.sign_in();await self.choose(pair)
            token=api.request('POST','/auth/login',{'email':'reviewer1@example.test','password':api.PASSWORD})[1]['token']
            status,_=api.request('POST','/reservations',dict(restaurant_id='r',table_id='a' if pair else 'c',starts_at_local=DAY+'T18:00',party_size=1),token,'competitor')
            self.assertEqual(status,201)
            await self.el('booking-party-size').fill('3')
            async with self.page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as response:
                await self.el('booking-submit').click()
            refusal=await response.value
            self.assertEqual(refusal.status,409)
            self.assertEqual((await refusal.json())['error']['code'],'table_unavailable')
            await self.assert_feedback('booking-error')
            await expect(self.el('booking-form')).to_be_visible();await expect(self.el('booking-party-size')).to_have_value('3')
            await expect(self.el('slot-a-18:00' if pair else 'slot-c-18:00')).to_have_attribute('data-available','false')
            if pair:await expect(self.el('slot-b+a-18:00')).to_have_count(0)
            await self.shot('pair-refused' if pair else 'single-refused')

    async def test_browser_05_lost_response_before_and_after_commit(self):
        for pair,commit in [(False,False),(False,True),(True,True)]:
            with self.subTest(pair=pair,commit=commit):
                api.request('POST','/_test/reset',self.seed);await self.sign_in();await self.choose(pair)
                captures=[];committed=[]
                async def lose(route):
                    captures.append((route.request.post_data,route.request.headers.get('idempotency-key')))
                    if len(captures)==1:
                        if commit:
                            response=await route.fetch();self.assertEqual(response.status,201);committed.append(await response.json())
                        await route.abort('failed')
                    else:await route.continue_()
                await self.page.route('**/reservations',lose)
                await self.el('booking-submit').click();await self.assert_feedback('booking-uncertain')
                await self.shot('pair-uncertain' if pair else ('single-uncertain-committed' if commit else 'single-uncertain-uncommitted'))
                await expect(self.el('booking-party-size')).to_have_value('4')
                await self.el('booking-submit').click();await expect(self.el('confirmation')).to_be_visible()
                self.assertEqual(captures[0],captures[1]);self.assertTrue(captures[0][1])
                if commit:await expect(self.el('confirmation-reference')).to_have_text(committed[0]['reference'])
                await expect(self.el('booking-uncertain')).to_have_count(0);await expect(self.el('booking-error')).to_have_count(0)
                token=api.request('POST','/auth/login',{'email':'reviewer0@example.test','password':api.PASSWORD})[1]['token']
                self.assertEqual(len(api.request('GET','/reservations',token=token)[1]['reservations']),1)
                await self.page.unroute('**/reservations',lose)

    async def test_browser_06_search_out_of_order(self):
        await self.sign_in();await self.page.goto(BASE+'/')
        release=asyncio.Event();started=asyncio.Event();delivered=asyncio.Event()
        async def delay(route):
            query=parse_qs(urlsplit(route.request.url).query)
            if query.get('restaurant_id')==['r']:
                response=await route.fetch();started.set();await release.wait()
                await route.fulfill(response=response);delivered.set()
            else:await route.continue_()
        await self.page.route('**/availability?*',delay)
        await self.el('restaurant-select').select_option('r');await self.el('date-input').fill(DAY)
        await self.el('party-size-input').fill('4');await self.el('search-button').click()
        await asyncio.wait_for(started.wait(),7)
        await self.shot('desktop-loading')
        await self.el('restaurant-select').select_option('other');await self.el('date-input').fill('2040-06-15')
        await self.el('party-size-input').fill('2');await self.el('search-button').click()
        await expect(self.el('slot-other_table-18:00')).to_be_visible()
        release.set();await asyncio.wait_for(delivered.wait(),7)
        await self.page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        await expect(self.el('slot-other_table-18:00')).to_be_visible();await expect(self.el('slot-c-18:00')).to_have_count(0)
        await self.el('slot-other_table-18:00').click()
        await expect(self.el('booking-summary')).to_contain_text('other')
        await expect(self.el('booking-party-size')).to_have_value('2')
        await expect(self.el('date-input')).to_have_value('2040-06-15')
        await self.page.unroute('**/availability?*',delay)

    async def test_browser_07_open_page_upgrade_recovers_old_receipt(self):
        # UI assets remain on Stage2; API routing starts on actual accepted Stage1.
        api.request('POST','/_test/reset',api.fixture(),base=OLD)
        api.request('POST','/_test/reset',self.seed,base=DEST)
        backend=[OLD];captured=[];original=[];lose=[True]
        async def proxy(route):
            path=urlsplit(route.request.url).path
            if path.startswith(('/auth/','/_test/','/restaurants','/availability','/reservations','/reservation-moves')):
                u=urlsplit(route.request.url);url=backend[0]+u.path+('?' +u.query if u.query else '')
                if path=='/reservations' and route.request.method=='POST':
                    captured.append((route.request.post_data,route.request.headers.get('idempotency-key')))
                    response=await route.fetch(url=url)
                    if lose[0]:
                        self.assertEqual(response.status,201);original.append(await response.json());lose[0]=False
                        await route.abort('failed');return
                    await route.fulfill(response=response);return
                response=await route.fetch(url=url);await route.fulfill(response=response)
            else:await route.continue_()
        await self.page.route('**/*',proxy)
        await self.sign_in();await self.search(party=3)
        await self.el('slot-t1-18:00').click();await self.el('booking-submit').click()
        await self.assert_feedback('booking-uncertain')
        snapshot=api.request('GET','/_test/export',base=OLD)[1]
        self.assertEqual(api.request('POST','/_test/import',snapshot,base=DEST)[0],204)
        backend[0]=DEST
        await self.el('booking-submit').click();await expect(self.el('confirmation-reference')).to_have_text(original[0]['reference'])
        self.assertEqual(captured[0],captured[1]);await expect(self.el('current-user')).to_contain_text('Reviewer 0')
        await self.page.goto(BASE+'/lookup');await self.el('lookup-reference-input').fill(original[0]['reference'])
        await self.el('lookup-submit').click();await expect(self.el('reservation-status')).to_have_text('confirmed')
        await self.page.unroute('**/*',proxy)

    async def test_browser_08_mobile_pair_form_and_confirmation(self):
        await self.page.set_viewport_size({'width':375,'height':812})
        await self.sign_in();await self.choose(True)
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await self.shot('mobile-pair-selected')
        await self.el('booking-submit').click();await expect(self.el('confirmation')).to_be_visible()
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        await self.shot('mobile-pair-confirmed')

    async def test_browser_09_long_restaurant_name_mobile(self):
        self.seed['restaurants'][0]['name']='Restaurantwithanexceptionallylongsinglewordname'
        api.request('POST','/_test/reset',self.seed)
        await self.page.set_viewport_size({'width':375,'height':812})
        await self.sign_in();await self.search()
        await self.shot('mobile-long-name-grid')
        dimensions=await self.page.evaluate('({scrollWidth:document.documentElement.scrollWidth,innerWidth})')
        print('LONG_NAME_DIMENSIONS '+json.dumps(dimensions),flush=True)
        self.assertLessEqual(dimensions['scrollWidth'],dimensions['innerWidth'])
        await self.el('slot-c-18:00').click();await self.el('booking-submit').click()
        await expect(self.el('confirmation')).to_be_visible()
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        ref=await self.el('confirmation-reference').inner_text()
        await self.page.goto(BASE+'/lookup?reference='+ref)
        await expect(self.el('reservation-detail')).to_be_visible()
        await self.shot('mobile-long-name-lookup')
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        self.seed['restaurants'][0]['opening_hours']=[]
        api.request('POST','/_test/reset',self.seed)
        await self.page.goto(BASE+'/')
        await self.el('restaurant-select').select_option('r');await self.el('date-input').fill(DAY)
        await self.el('search-button').click();await expect(self.el('no-slots')).to_be_visible()
        await self.shot('mobile-long-name-empty')
        self.assertTrue(await self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    async def test_browser_10_signup_errors_and_lookup_refusal(self):
        await self.page.goto(BASE+'/signup')
        for field,value in [('signup-email','reviewer0@example.test'),('signup-password',api.PASSWORD),('signup-display-name','New guest')]:
            await self.el(field).fill(value)
        await self.el('signup-submit').click();await expect(self.el('auth-error')).to_be_visible()
        await self.el('signup-email').fill('newguest@example.test')
        await self.el('signup-submit').click();await self.page.wait_for_url(BASE+'/')
        await expect(self.el('current-user')).to_contain_text('New guest')
        await self.page.goto(BASE+'/lookup');await self.el('lookup-reference-input').fill('UNKNOWN1')
        await self.el('lookup-submit').click();await expect(self.el('reservation-error')).to_be_visible()
        past=dict(restaurant_id='r',table_id='c',starts_at_local='2000-06-14T18:00',party_size=2)
        status,record=api.request('POST','/reservations',past,self.token,'past-cutoff');self.assertEqual(status,201)
        await self.el('lookup-reference-input').fill(record['reference']);await self.el('lookup-submit').click()
        await expect(self.el('reservation-error')).to_be_visible();await expect(self.el('reservation-detail')).to_have_count(0)
        await self.sign_in();await self.page.goto(BASE+'/lookup?reference='+record['reference'])
        await expect(self.el('reservation-status')).to_have_text('confirmed')
        await self.el('reservation-cancel-button').click();await expect(self.el('reservation-error')).to_be_visible()
        await expect(self.el('reservation-status')).to_have_text('confirmed')
        await self.shot('lookup-cutoff-refused')
