'use strict';

// Each asynchronous operation captures its session, route and interaction object.
// Only that exact live context may publish success, failure or cleanup.
const main = document.querySelector('main');
const sessionKey = 'tablekeeper.session.v1';
let session = null;
try { session = ExactJSON.parse(localStorage.getItem(sessionKey) || 'null'); } catch (_) { /* no retained session */ }
if (!session || typeof session.token !== 'string' || typeof session.user_id !== 'string') session = null;
let sessionVersion = 0, routeVersion = 0, searchVersion = 0, lookupVersion = 0;
let restaurants = [], restaurantLoad = null;
let results = null, selection = null, lookupDetail = null;
let lookupText = '', bookingSerial = 0;
const today = new Date();
const draft = {restaurant_id: '', date: `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`, party_size: '2'};

function node(tag, attrs = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'class') element.className = value;
    else if (key.startsWith('on')) element.addEventListener(key.slice(2), value);
    else element.setAttribute(key, value === true ? '' : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined) element.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return element;
}
const test = (id) => ({'data-testid': id});
function field(label, input) { return node('div', {class:'field'}, node('label', {for:input.id}, label), input); }
function notice(text, kind='info', id=null) {
  return node('div', {class:`notice ${kind}`, role:kind === 'error' || kind === 'uncertain' ? 'alert' : 'status', ...(id ? test(id) : {})}, text);
}
function memberIds(record) { return record.table_ids || [record.table_id]; }
function tableLabels(restaurant, ids) { return ids.map(id => restaurant.tables.find(t => t.id === id)?.label || 'Table').join(' + '); }
function localText(local) { return local.replace('T', ' at '); }
function message(error) {
  const known = {table_unavailable:'That seating option was just reserved. Your choices are saved below; please choose another table or time.',
    party_exceeds_capacity:'This seating option is too small for your party. Choose a larger table or a table pair.',
    unauthenticated:'Please sign in to continue with this reservation.', not_found:'We could not find that reservation for your account. Check the reference and try again.',
    cutoff_passed:'This reservation is now within the restaurant’s cancellation window and cannot be cancelled.',
    email_taken:'An account already uses this email. Please sign in instead.', validation_failed:'Please check the details and try again.',
    outside_opening_hours:'This time is outside the restaurant’s opening hours.', invalid_local_time:'This local time is not available because the clocks change that day.'};
  return known[error.code] || error.message || 'Something went wrong. Please try again.';
}
class RequestError extends Error {
  constructor(status, code, text) { super(text); this.status = status; this.code = code; }
}
async function api(path, {method='GET', body, token, key} = {}) {
  const headers = {'Accept':'application/json'};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  if (key) headers['Idempotency-Key'] = key;
  const response = await fetch(path, {method, headers, body:body === undefined ? undefined : typeof body === 'string' ? body : ExactJSON.stringify(body)});
  let data;
  try { data = ExactJSON.parse(await response.text()); }
  catch (error) {
    if (response.status >= 400 && response.status < 500) throw new RequestError(response.status, '', 'The request was refused. Please check your details.');
    throw error;
  }
  if (!response.ok) {
    if (response.status >= 500) throw new Error('The service could not confirm the outcome.');
    throw new RequestError(response.status, data.error?.code, data.error?.message);
  }
  return data;
}
function saveSession(value) {
  session = value; sessionVersion++; selection = null; lookupDetail = null; lookupVersion++;
  try { if (value) localStorage.setItem(sessionKey, ExactJSON.stringify(value)); else localStorage.removeItem(sessionKey); } catch (_) { /* current page still works */ }
  renderAccount();
}
function renderAccount() {
  const account = document.querySelector('#account');
  account.replaceChildren();
  if (session) {
    account.append(node('span', {class:'user-name', ...test('current-user')}, session.display_name),
      node('button', {type:'button', class:'text-button', ...test('logout-button'), onclick:()=>{ saveSession(null); navigate(location.pathname); }}, 'Sign out'));
  } else account.append(node('a', {href:'/login', 'data-nav':''}, 'Sign in'), node('a', {href:'/signup', 'data-nav':''}, 'Join us'));
  for (const link of document.querySelectorAll('nav a')) {
    if (link.getAttribute('href') === location.pathname) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  }
}
function navigate(path, replace=false) {
  if (replace) history.replaceState({}, '', path); else if (location.pathname + location.search !== path) history.pushState({}, '', path);
  routeVersion++; searchVersion++; lookupVersion++; selection = null; lookupDetail = null;
  renderRoute();
}
document.addEventListener('click', event => {
  const anchor = event.target.closest('a[data-nav]');
  if (!anchor || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  event.preventDefault(); navigate(anchor.getAttribute('href'));
});
window.addEventListener('popstate', ()=>{ routeVersion++; searchVersion++; lookupVersion++; selection=null; lookupDetail=null; renderRoute(); });

async function loadRestaurants() {
  if (!restaurantLoad) restaurantLoad = api('/restaurants').then(data => { restaurants = data.restaurants; return restaurants; }).catch(error => {restaurantLoad=null; throw error;});
  return restaurantLoad;
}
function renderRoute() {
  renderAccount(); main.replaceChildren();
  if (location.pathname === '/signup' || location.pathname === '/login') renderAuth(location.pathname === '/signup');
  else if (location.pathname === '/lookup') renderLookup();
  else renderHome();
}
function renderHome() {
  const route = routeVersion;
  const hero = node('section', {class:'hero'}, node('div', {}, node('p', {class:'eyebrow'}, 'Make time for good company'),
    node('h1', {}, 'A lovely evening', node('br'), 'starts here.'), node('p', {class:'muted'}, 'Find your place, bring your people, and let the evening unfold. A table for two or a little more room — it’s yours to choose.')),
    node('figure', {class:'hero-art'}, node('img', {src:'/static/table.svg', alt:'', width:'400', height:'240'}), node('figcaption', {}, 'A PLACE FOR YOUR NEXT GATHERING')));
  const select = node('select', {id:'restaurant', ...test('restaurant-select'), required:true}, node('option', {value:''}, 'Loading restaurants…'));
  const date = node('input', {id:'date', type:'date', value:draft.date, required:true, ...test('date-input')});
  const party = node('input', {id:'party', type:'number', min:'1', step:'any', value:draft.party_size, required:true, inputmode:'numeric', ...test('party-size-input')});
  const submit = node('button', {type:'submit', class:'primary', ...test('search-button')}, 'Find a table', node('span', {'aria-hidden':'true'}, '↗'));
  const form = node('form', {class:'search-fields', novalidate:true, onsubmit:event=>{event.preventDefault(); runSearch();}},
    field('Restaurant', select), field('Date', date), field('Guests', party), submit);
  for (const [element, key] of [[select,'restaurant_id'], [date,'date'], [party,'party_size']]) element.addEventListener('input', ()=>{
    draft[key] = element.value; searchVersion++; results = null; selection = null;
    document.querySelector('#search-feedback')?.replaceChildren();
    document.querySelector('#results')?.replaceChildren(); document.querySelector('#booking')?.replaceChildren();
  });
  main.append(hero, node('section', {class:'search-panel', 'aria-label':'Find a table'}, form,
    node('p', {class:'form-help'}, node('span', {class:'small-dot', 'aria-hidden':'true'}), 'Choose a restaurant, then explore its tables and available times.')),
    node('div', {id:'search-feedback', 'aria-live':'polite'}), node('section', {id:'results', 'aria-label':'Available seating'}), node('section', {id:'booking', 'aria-label':'Your booking'}));
  loadRestaurants().then(list=>{
    if (route !== routeVersion || !select.isConnected) return;
    select.replaceChildren(...list.map(r=>node('option',{value:r.id},r.name)));
    if (!list.length) {
      select.append(node('option',{value:''},'No restaurants available'));
      document.querySelector('#search-feedback').append(notice('There are no restaurants available to book yet. Please check again later.'));
    } else {
      if (!list.some(r=>r.id===draft.restaurant_id)) draft.restaurant_id=list[0].id;
      select.value=draft.restaurant_id;
      if (results) renderResults();
    }
  }).catch(error=>{
    if (route !== routeVersion || !select.isConnected) return;
    select.replaceChildren(node('option',{value:''},'Restaurants unavailable'));
    document.querySelector('#search-feedback').replaceChildren(notice('We could not load restaurants. Please reload to try again.', 'error'));
  });
}
async function runSearch(refresh=false) {
  const route = routeVersion, version = ++searchVersion, query = {...draft};
  const feedback = document.querySelector('#search-feedback');
  if (!feedback) return;
  const valid = ()=>route === routeVersion && version === searchVersion && feedback.isConnected;
  if (!refresh) { results=null; selection=null; document.querySelector('#results').replaceChildren(); document.querySelector('#booking').replaceChildren(); }
  try { query.party_size = ExactJSON.positiveInteger(query.party_size).toString(); }
  catch (error) { feedback.replaceChildren(notice(message(error), 'error')); return; }
  feedback.replaceChildren(notice(refresh ? 'Updating availability. Your booking details are saved.' : 'Finding a place for your party…','loading'));
  try {
    const params = new URLSearchParams(query);
    const [restaurant, availability] = await Promise.all([api('/restaurants/'+encodeURIComponent(query.restaurant_id)), api('/availability?'+params)]);
    if (!valid()) return;
    results = {query, restaurant, availability}; feedback.replaceChildren(); renderResults();
  } catch (error) {
    if (!valid()) return;
    feedback.replaceChildren(notice(refresh ? 'We could not refresh availability. Your form is saved; search again when you are ready.' : message(error), 'error'));
  }
}
function renderResults() {
  const container = document.querySelector('#results');
  if (!container || !results) return;
  const {restaurant, availability, query} = results;
  container.replaceChildren();
  if (!availability.slots.length) {
    container.append(node('div', {class:'empty-state', ...test('no-slots')}, node('h2',{},'Another day, perhaps?'), node('p',{},`${restaurant.name} has no booking times on ${query.date}. Choose another date to find your table.`)));
    return;
  }
  container.append(node('div',{class:'results-head'},node('div',{},node('p',{class:'eyebrow'},'A place at the table'),node('h2',{},'Choose your seating'),
    node('p',{class:'results-context'},`${restaurant.name} · ${query.date} · ${query.party_size} guests`),node('p',{class:'muted'},`Times are local to ${restaurant.timezone}.`)),
    node('div',{class:'legend'},node('span',{},'Available'),node('span',{},'Unavailable'))));
  const grid = node('div',{class:'availability-grid',...test('availability-grid')});
  // Capacity comes from this availability result. Restaurant detail intentionally
  // remains its original fixture after a dated policy is published.
  const capacityFor = ids => availability.slots.flatMap(s=>s.available_options||[])
    .find(o=>JSON.stringify(o.table_ids)===JSON.stringify(ids))?.capacity;
  const options = restaurant.tables.map(t=>({ids:[t.id],capacity:capacityFor([t.id])}));
  for (const pair of restaurant.combinable || []) {
    if (availability.slots.some(s=>(s.available_options||[]).some(o=>JSON.stringify(o.table_ids)===JSON.stringify(pair))))
      options.push({ids:pair,capacity:capacityFor(pair)});
  }
  for (const option of options) {
    const labels = tableLabels(restaurant,option.ids), pair=option.ids.length===2;
    const buttons = availability.slots.map(slot=>{
      const time=slot.starts_at_local.slice(11);
      const available=pair ? (slot.available_options||[]).some(o=>JSON.stringify(o.table_ids)===JSON.stringify(option.ids)) : slot.available_table_ids.includes(option.ids[0]);
      const selected=selection && selection.restaurant.id===restaurant.id && selection.local===slot.starts_at_local && JSON.stringify(selection.ids)===JSON.stringify(option.ids);
      return node('button',{type:'button',class:'slot',...test(`slot-${option.ids.join('+')}-${time}`),'data-available':String(available),
        'aria-label':`${labels}, ${time}, ${available?'available':'unavailable'}`,'aria-pressed':String(Boolean(selected)), disabled:!available,
        onclick:()=>choose(restaurant,option.ids,slot,query)},time);
    });
    grid.append(node('article',{class:`seating-card ${pair?'pair':''}`},node('div',{class:'seating-heading'},node('div',{},node('p',{class:'seating-kind'},pair?'Tables together':'Your own table'),
      node('h3',{},labels)),option.capacity===undefined?null:node('span',{class:'seating-capacity'},`Up to ${option.capacity}`)),node('div',{class:'slot-list'},buttons)));
  }
  container.append(grid);
  if (!availability.slots.some(s=>(s.available_options||s.available_table_ids).length)) container.append(notice('No tables fit your party at these times. Try another date or a different party size.'));
}
function choose(restaurant, ids, slot, query) {
  if (!session) {
    document.querySelector('#search-feedback').replaceChildren(notice('Please sign in or create an account to reserve this table.','error','auth-error'));
    return;
  }
  document.querySelector('#search-feedback').replaceChildren();
  if (!(selection && selection.restaurant.id===restaurant.id && selection.local===slot.starts_at_local && JSON.stringify(selection.ids)===JSON.stringify(ids))) {
    selection={id:++bookingSerial,restaurant,ids:[...ids],local:slot.starts_at_local,party:query.party_size,revision:0,intent:null,busy:false,error:null,uncertain:false,receipt:null};
    renderBooking();
  }
  renderResults();
  document.querySelector('#booking')?.scrollIntoView({block:'nearest'});
  document.querySelector('#booking-party')?.focus({preventScroll:true});
}
function renderBooking() {
  const container=document.querySelector('#booking'); if (!container) return;
  container.replaceChildren(); if (!selection) return;
  const current=selection;
  const party=node('input',{id:'booking-party',type:'number',min:'1',step:'any',required:true,value:current.party,...test('booking-party-size')});
  const submit=node('button',{class:'primary',type:'submit',...test('booking-submit')},'Confirm reservation');
  party.addEventListener('input',()=>{
    if (selection!==current) return;
    current.party=party.value; current.revision++; current.intent=null; current.busy=false; current.error=null; current.uncertain=false; current.receipt=null;
    renderBookingFeedback();
  });
  container.append(node('div',{class:'booking-panel',...test('booking-form')},node('div',{class:'booking-top'},node('div',{},node('p',{class:'eyebrow'},'Your evening, coming together'),
    node('h2',{},'Make it a reservation'),node('p',{class:'booking-summary',...test('booking-summary')},`${tableLabels(current.restaurant,current.ids)} · ${localText(current.local)}`))),
    node('form',{class:'booking-fields',novalidate:true,onsubmit:event=>{event.preventDefault(); submitBooking();}},field('Guests at your table',party),submit),
    node('p',{class:'booking-note'},`Local time at ${current.restaurant.name}. Your confirmation includes the cancellation terms accepted for this booking.`),
    node('div',{id:'booking-feedback','aria-live':'polite'})));
  renderBookingFeedback();
}
function renderBookingFeedback() {
  const current=selection, box=document.querySelector('#booking-feedback'), button=document.querySelector('[data-testid="booking-submit"]');
  if (!current || !box || !button) return;
  button.disabled=current.busy;
  button.textContent=current.busy?'Sending reservation…':current.uncertain?'Retry reservation':current.receipt?'View confirmation again':'Confirm reservation';
  box.replaceChildren();
  if (current.busy) box.append(notice('Your reservation is being sent.','loading'));
  if (current.error) box.append(notice(current.error,'error','booking-error'));
  if (current.uncertain) box.append(notice('We could not confirm whether your reservation was received. Keep these details and retry to safely retrieve the original result.','uncertain','booking-uncertain'));
  if (current.receipt) {
    const record=current.receipt, labels=tableLabels(current.restaurant,memberIds(record));
    box.append(node('section',{class:'confirmation',...test('confirmation')},node('p',{class:'eyebrow'},'We’ll save you a seat'),node('h3',{},'Your table is reserved.'),
      node('p',{...test('confirmation-details')},`${current.restaurant.name} · ${labels} · ${localText(record.starts_at_local)} · ${record.party_size} guests`),
      node('p',{...test('confirmation-tables')},labels),node('span',{class:'quiet'},'Your confirmation reference'),
      node('strong',{class:'reference',...test('confirmation-reference')},record.reference),
      record.accepted_terms?node('p',{class:'quiet'},`Cancellation closes ${record.accepted_terms.cancellation_cutoff_minutes} minutes before your reservation.`):null,
      node('a',{href:'/lookup?reference='+encodeURIComponent(record.reference),'data-nav':''},'View or cancel this reservation →')));
  }
}
async function submitBooking() {
  const current=selection; if (!current || current.busy) return;
  if (!session) { current.error='Please sign in before reserving a table.'; renderBookingFeedback(); return; }
  const revision=current.revision, route=routeVersion, identity=sessionVersion;
  const valid=()=>selection===current && current.revision===revision && routeVersion===route && sessionVersion===identity;
  let partySize;
  try { partySize=ExactJSON.positiveInteger(current.party); }
  catch (error) { current.error=message(error); current.uncertain=false; current.receipt=null; renderBookingFeedback(); return; }
  const body={restaurant_id:current.restaurant.id, ...(current.ids.length===1?{table_id:current.ids[0]}:{table_ids:[...current.ids]}), starts_at_local:current.local, party_size:partySize};
  const encoded=ExactJSON.stringify(body);
  if (!current.intent || current.intent.body!==encoded || current.intent.user!==session.user_id)
    current.intent={key:crypto.randomUUID(),body:encoded,user:session.user_id,token:session.token};
  const intent=current.intent;
  current.busy=true; current.error=null; current.uncertain=false; current.receipt=null; renderBookingFeedback();
  try {
    const record=await api('/reservations',{method:'POST',body:intent.body,token:intent.token,key:intent.key});
    if (!record || typeof record.reference!=='string') throw new Error('Incomplete confirmation');
    if (!valid()) return;
    current.receipt=record;
  } catch (error) {
    if (!valid()) return;
    if (error instanceof RequestError) {
      current.error=message(error);
      if (error.code==='table_unavailable') runSearch(true);
    } else current.uncertain=true;
  } finally {
    if (valid()) { current.busy=false; renderBookingFeedback(); }
  }
}

function renderAuth(signup) {
  const route=routeVersion, identity=sessionVersion;
  let version=0, pending=false;
  const email=node('input',{id:'auth-email',type:'email',autocomplete:'email',required:true,...test(signup?'signup-email':'login-email')});
  const password=node('input',{id:'auth-password',type:'password',minlength:'8',autocomplete:signup?'new-password':'current-password',required:true,...test(signup?'signup-password':'login-password')});
  const name=node('input',{id:'auth-name',type:'text',autocomplete:'name',required:true,...test('signup-display-name')});
  const feedback=node('div',{'aria-live':'polite'});
  const submit=node('button',{class:'primary',type:'submit',...test(signup?'signup-submit':'login-submit')},signup?'Create your account':'Sign in');
  const form=node('form',{},signup?field('Your name',name):null,field('Email address',email),field('Password',password),submit,feedback);
  for (const input of [email,password,name]) input.addEventListener('input',()=>{version++; pending=false; submit.disabled=false; feedback.replaceChildren();});
  form.addEventListener('submit',async event=>{
    event.preventDefault(); if (pending) return;
    const request=++version, valid=()=>routeVersion===route && sessionVersion===identity && version===request && form.isConnected;
    pending=true; submit.disabled=true; feedback.replaceChildren(notice('Signing you in…','loading'));
    try {
      const body={email:email.value,password:password.value,...(signup?{display_name:name.value}:{})};
      const value=await api(signup?'/auth/signup':'/auth/login',{method:'POST',body});
      if (!valid()) return;
      saveSession(value); navigate('/');
    } catch (error) { if (valid()) feedback.replaceChildren(notice(message(error),'error','auth-error')); }
    finally { if (valid()) {pending=false; submit.disabled=false;} }
  });
  main.append(node('section',{class:'auth-layout'},node('div',{class:'auth-copy'},node('p',{class:'eyebrow'},signup?'There’s a place for you':'Welcome back'),
    node('h1',{},signup?'Good evenings.\nGreat company.':'Your next evening\nawaits.'),node('p',{},signup?'Make a little room for the moments that matter. Create an account to reserve and manage your tables.':'Sign in to save your seat, find a reservation, or make room for a new plan.')),
    node('div',{class:'auth-card'},node('h2',{},signup?'Join the table':'Come on in'),form,node('p',{class:'switch-auth'},signup?'Already joining us? ':'New to Tablekeeper? ',
      node('a',{href:signup?'/login':'/signup','data-nav':''},signup?'Sign in':'Create an account')))));
}
function renderLookup() {
  const initial=new URLSearchParams(location.search).get('reference');
  if (initial) lookupText=initial;
  const input=node('input',{id:'lookup-reference',type:'text',value:lookupText,required:true,autocomplete:'off',...test('lookup-reference-input')});
  const submit=node('button',{type:'submit',class:'primary',...test('lookup-submit')},'Find reservation');
  input.addEventListener('input',()=>{
    lookupText=input.value; lookupVersion++; lookupDetail=null;
    document.querySelector('#lookup-feedback').replaceChildren(); document.querySelector('#lookup-detail').replaceChildren();
  });
  main.append(node('section',{class:'lookup-shell'},node('p',{class:'eyebrow'},'Your place is kept'),node('h1',{},'A reservation to return to.'),
    node('p',{class:'muted'},'Enter your confirmation reference to find the details or cancel your table.'),
    node('div',{class:'search-panel'},node('form',{class:'lookup-form',onsubmit:event=>{event.preventDefault(); lookup();}},field('Confirmation reference',input),submit),
      node('div',{id:'lookup-feedback','aria-live':'polite'}),node('div',{id:'lookup-detail'}))));
}
async function lookup() {
  const route=routeVersion, identity=sessionVersion, version=++lookupVersion;
  const feedback=document.querySelector('#lookup-feedback'); if (!feedback) return;
  lookupDetail=null; document.querySelector('#lookup-detail').replaceChildren();
  if (!session) { feedback.replaceChildren(notice('Please sign in to look up your reservation.','error','reservation-error')); return; }
  const token=session.token, ref=lookupText.trim(), valid=()=>routeVersion===route && sessionVersion===identity && lookupVersion===version && feedback.isConnected;
  feedback.replaceChildren(notice('Finding your reservation…','loading'));
  try {
    const record=await api('/reservations/'+encodeURIComponent(ref),{token});
    const restaurant=await api('/restaurants/'+encodeURIComponent(record.restaurant_id));
    if (!valid()) return;
    lookupDetail={record,restaurant,version}; feedback.replaceChildren(); renderDetail();
  } catch (error) { if (valid()) feedback.replaceChildren(notice(message(error),'error','reservation-error')); }
}
function renderDetail() {
  const container=document.querySelector('#lookup-detail'), current=lookupDetail; if (!container || !current) return;
  const {record,restaurant}=current, labels=tableLabels(restaurant,memberIds(record));
  const lines=node('dl',{class:'detail-lines'},node('div',{},node('dt',{},'Your tables'),node('dd',{...test('reservation-tables')},labels)),
    node('div',{},node('dt',{},'Date & local time'),node('dd',{},localText(record.starts_at_local))),node('div',{},node('dt',{},'Guests'),node('dd',{},record.party_size)),
    node('div',{},node('dt',{},'Reference'),node('dd',{},record.reference)));
  const detail=node('section',{class:'detail',...test('reservation-detail')},node('div',{class:'detail-heading'},node('h2',{},restaurant.name),
    node('span',{class:`status ${record.status}`,...test('reservation-status')},record.status)),lines);
  if (record.status==='confirmed') detail.append(node('button',{type:'button',class:'secondary danger',...test('reservation-cancel-button'),onclick:event=>cancel(current,event.currentTarget)},'Cancel reservation'),
    node('p',{class:'quiet'},record.accepted_terms?`Cancellation closes ${record.accepted_terms.cancellation_cutoff_minutes} minutes before your reservation.`:'Cancellation follows the terms accepted when you booked.'));
  else detail.append(node('p',{class:'muted'},'This reservation is cancelled. We hope to welcome you another time.'));
  container.replaceChildren(detail);
}
async function cancel(current,button) {
  if (!session || button.disabled) return;
  const route=routeVersion, identity=sessionVersion, version=lookupVersion, token=session.token;
  const valid=()=>routeVersion===route && sessionVersion===identity && lookupVersion===version && lookupDetail===current;
  button.disabled=true; button.textContent='Cancelling…';
  document.querySelector('#lookup-feedback').replaceChildren();
  try {
    const record=await api('/reservations/'+encodeURIComponent(current.record.reference)+'/cancel',{method:'POST',body:{},token});
    if (!valid()) return;
    current.record=record; renderDetail();
  } catch (error) {
    if (valid()) document.querySelector('#lookup-feedback').replaceChildren(notice(message(error),'error','reservation-error'));
  } finally { if (valid() && button.isConnected) {button.disabled=false; button.textContent='Cancel reservation';} }
}
renderRoute();
