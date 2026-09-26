'use strict';
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let session;
try { session = JSON.parse(localStorage.getItem('tablekeeper-session') || 'null'); } catch { session = null; }
const state = { epoch: 0, bookingVersion: 0, restaurant: null, searched: null, data: null, selected: null, attempt: null };
const route = location.pathname;
document.querySelector(`[data-nav="${route}"]`)?.setAttribute('aria-current','page');
function account() {
  $('account').innerHTML = session ? `<span data-testid="current-user">${esc(session.display_name)}</span><button class="link-button" data-testid="logout-button" id="logout">Sign out</button>` : '<a href="/login">Sign in</a><a href="/signup">Join</a>';
  if ($('logout')) $('logout').onclick = () => { localStorage.removeItem('tablekeeper-session'); session = null; location.href = '/'; };
}
account();
async function api(path, options = {}) {
  const headers = {'Content-Type':'application/json; charset=utf-8', ...(session ? {'Authorization':`Bearer ${session.token}`} : {}), ...options.headers};
  let response, data;
  try { response = await fetch(path, {...options, headers}); data = await response.json(); }
  catch { throw {message:'We could not receive a response. Please try again.', uncertain:true}; }
  if (!response.ok) throw {message:data.error?.message || 'We could not complete that request.', code:data.error?.code, uncertain:response.status >= 500};
  return data;
}
function status(id, testid, message, type='error', title='') {
  $(id).innerHTML = `<div class="status ${type}" data-testid="${testid}" role="${type === 'error' ? 'alert':'status'}">${title ? `<strong>${esc(title)}</strong><p>${esc(message)}</p>` : esc(message)}</div>`;
}
const labels = (restaurant, ids) => ids.map(id => restaurant.tables.find(t => t.id === id)?.label || id).join(' + ');
const idsOf = (record) => record.table_ids || [record.table_id];
const friendlyDate = (date) => new Date(date+'T12:00:00').toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long'});
function key() { const a = new Uint8Array(16); crypto.getRandomValues(a); return Array.from(a, n => n.toString(16).padStart(2,'0')).join(''); }
function resetBooking() { state.bookingVersion++; state.selected = null; state.attempt = null; $('booking').innerHTML = ''; }
function drawGrid() {
  const r = state.restaurant, d = state.data, q = state.searched;
  if (!d.slots.length) { $('results').innerHTML = `<div class="empty" data-testid="no-slots"><h2>A quiet day.</h2><p>${esc(r.name)} has no booking times on ${esc(friendlyDate(q.date))}. Try another date.</p></div>`; return; }
  $('results').innerHTML = `<div class="results-head"><div><h2>${esc(r.name)}</h2><p>${esc(friendlyDate(q.date))} · ${esc(q.party_size)} guests · local restaurant time</p></div><div class="legend"><span>Available</span><span>Unavailable</span></div></div><div data-testid="availability-grid" id="grid"></div>`;
  for (const slot of d.slots) {
    const row = document.createElement('section'); row.className = 'slot-row';
    const time = slot.starts_at_local.slice(11,16);
    row.innerHTML = `<div class="slot-time">${esc(time)}</div><div class="seats"></div>`;
    const options = r.tables.map(t => ({table_ids:[t.id],capacity:t.capacity,available:slot.available_table_ids.includes(t.id)}));
    for (const option of slot.available_options || []) if (option.table_ids.length === 2) options.push({...option,available:true});
    for (const option of options) {
      const ids = option.table_ids, name = labels(r, ids), button = document.createElement('button');
      button.className = 'seat' + (ids.length > 1 ? ' pair':'');
      button.dataset.testid = `slot-${ids.join('+')}-${time}`; button.dataset.available = String(option.available); button.disabled = !option.available;
      const selected = state.selected && state.selected.starts_at_local === slot.starts_at_local && JSON.stringify(state.selected.ids) === JSON.stringify(ids);
      button.setAttribute('aria-pressed',String(Boolean(selected)));
      button.innerHTML = `<strong>${esc(name)}</strong><span>${ids.length > 1 ? 'Tables together · ' : ''}Seats ${option.capacity}</span><span class="seat-status">${selected ? 'Selected' : option.available ? 'Choose this table' : 'Unavailable'}</span>`;
      button.onclick = () => {
        if (!session) { status('search-feedback','auth-error','Sign in or create an account to reserve your table.'); return; }
        state.bookingVersion++; state.attempt = null;
        state.selected = {restaurant:r, ids:[...ids], starts_at_local:slot.starts_at_local, party_size:Number(q.party_size)};
        $('search-feedback').innerHTML = ''; renderBooking(); drawGrid();
        $('booking').scrollIntoView({block:'nearest',behavior:'smooth'});
      };
      row.querySelector('.seats').append(button);
    }
    $('grid').append(row);
  }
}
async function search(keepBooking=false, saved=null) {
  const q = saved || {restaurant_id:$('restaurant').value,date:$('date').value,party_size:$('party').value};
  const epoch = ++state.epoch;
  if (!keepBooking) resetBooking();
  $('search-feedback').innerHTML = ''; $('results').innerHTML = '<div class="loading" role="status">Finding your place…</div>';
  try {
    const [data, restaurant] = await Promise.all([api('/availability?'+new URLSearchParams(q)),api('/restaurants/'+encodeURIComponent(q.restaurant_id))]);
    if (epoch !== state.epoch) return;
    state.restaurant = restaurant; state.searched = {...q}; state.data = data; drawGrid();
  } catch(error) { if (epoch === state.epoch) { $('results').innerHTML = ''; status('search-feedback','search-error',error.message); } }
}
function renderBooking() {
  const selection = state.selected;
  $('booking').innerHTML = `<section class="card booking-card" data-testid="booking-form"><div class="eyebrow">Your selection</div><h2>A table for you.</h2><div class="booking-summary" data-testid="booking-summary">${esc(selection.restaurant.name)}<br><strong>${esc(labels(selection.restaurant,selection.ids))}</strong><br>${esc(selection.starts_at_local.replace('T',' · '))}</div><form id="book"><label for="booking-party">Number of guests</label><input id="booking-party" data-testid="booking-party-size" type="number" min="1" step="1" required value="${selection.party_size}"><button class="primary" data-testid="booking-submit">Confirm reservation</button></form><p class="fine">Your table is reserved only when a confirmation appears below.</p><div id="booking-feedback"></div><div id="confirmation-area"></div></section>`;
  $('booking-party').oninput = () => { state.attempt = null; $('confirmation-area').innerHTML = ''; $('booking-feedback').innerHTML = ''; };
  $('book').onsubmit = async event => {
    event.preventDefault(); const version = state.bookingVersion, user = session?.user_id;
    const body = {restaurant_id:selection.restaurant.id,starts_at_local:selection.starts_at_local,party_size:Number($('booking-party').value),...(selection.ids.length === 1 ? {table_id:selection.ids[0]} : {table_ids:selection.ids})};
    const encoded = JSON.stringify(body);
    if (!state.attempt || state.attempt.body !== encoded || state.attempt.user !== user) state.attempt = {key:key(),body:encoded,user};
    const attempt = state.attempt, button = $('book').querySelector('button'), partyInput = $('booking-party'); button.disabled = true; partyInput.disabled = true; button.textContent = 'Reserving…';
    $('confirmation-area').innerHTML = ''; $('booking-feedback').innerHTML = '<div class="loading" role="status">Checking your table…</div>';
    try {
      const reservation = await api('/reservations',{method:'POST',body:attempt.body,headers:{'Idempotency-Key':attempt.key}});
      if (version !== state.bookingVersion || user !== session?.user_id) return;
      $('booking-feedback').innerHTML = '';
      $('confirmation-area').innerHTML = `<section class="confirmation" data-testid="confirmation" aria-live="polite"><div class="eyebrow">Reservation confirmed</div><div class="reference" data-testid="confirmation-reference">${esc(reservation.reference)}</div><p data-testid="confirmation-details">${esc(selection.restaurant.name)} · ${esc(labels(selection.restaurant,idsOf(reservation)))} · ${esc(reservation.starts_at_local.replace('T',' '))}</p><p data-testid="confirmation-tables">${esc(labels(selection.restaurant,idsOf(reservation)))}</p><p class="success status">Your place is saved. Keep this reference for your visit.</p><a href="/lookup?reference=${encodeURIComponent(reservation.reference)}">View your reservation</a></section>`;
    } catch(error) {
      if (version !== state.bookingVersion || user !== session?.user_id) return;
      if (error.uncertain) status('booking-feedback','booking-uncertain','The response did not arrive, so your table may already be reserved. Keep these details and try again to recover the same reservation.','uncertain','Confirmation not received');
      else {
        status('booking-feedback','booking-error',error.code === 'table_unavailable' ? 'Someone just booked this seating. Your details are saved; choose another available table or time.' : error.message,'error','Reservation not made');
        if (error.code === 'table_unavailable') await search(true, state.searched);
      }
    } finally { if (version === state.bookingVersion && $('book')) { button.disabled = false; partyInput.disabled = false; button.textContent = 'Confirm reservation'; } }
  };
}
async function home() {
  $('app').innerHTML = `<section class="intro"><div class="eyebrow">Make room for a good evening</div><h1>Find your place<br>at the table.</h1><p>A quiet dinner or everyone together. Choose a restaurant, find your time, and make it yours.</p></section><form id="search" class="search-panel"><div><label for="restaurant">Restaurant</label><select id="restaurant" data-testid="restaurant-select" required><option value="">Loading restaurants…</option></select></div><div><label for="date">Date</label><input id="date" data-testid="date-input" type="date" required></div><div><label for="party">Guests</label><input id="party" data-testid="party-size-input" type="number" min="1" step="1" value="2" required></div><button class="primary" data-testid="search-button">Find a table</button></form><p class="search-note">Times are shown in each restaurant’s local time. Seating is confirmed at booking.</p><div id="search-feedback"></div><div class="flow"><section id="results" aria-live="polite"><div class="empty"><h2>Where shall we meet?</h2><p>Choose your date and party size to see available seating.</p></div></section><aside id="booking"></aside></div>`;
  const now = new Date(); $('date').value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  $('search').onsubmit = e => { e.preventDefault(); search(); };
  try { const data = await api('/restaurants'); $('restaurant').innerHTML = data.restaurants.map(r => `<option value="${esc(r.id)}">${esc(r.name)}</option>`).join(''); if (!data.restaurants.length) { $('restaurant').innerHTML = '<option value="">No restaurants available</option>'; $('results').innerHTML = '<div class="empty"><h2>No restaurants yet.</h2><p>Please check back when a restaurant is available for booking.</p></div>'; } }
  catch(e) { status('search-feedback','search-error',e.message); }
}
function auth(signup) {
  const prefix = signup ? 'signup':'login';
  $('app').innerHTML = `<div class="auth-layout"><section class="intro"><div class="eyebrow">You’re welcome here</div><h1>${signup ? 'More good<br>evenings ahead.' : 'A familiar<br>place to return.'}</h1><p>${signup ? 'Create an account to reserve your table and keep your plans close.' : 'Sign in to make a reservation or find the details of your next visit.'}</p></section><section class="card"><h2>${signup ? 'Join the table' : 'Welcome back'}</h2><form id="auth" class="stack">${signup ? '<div><label for="name">Your name</label><input id="name" data-testid="signup-display-name" autocomplete="name" required></div>':''}<div><label for="email">Email address</label><input id="email" data-testid="${prefix}-email" type="email" autocomplete="email" required></div><div><label for="password">Password</label><input id="password" data-testid="${prefix}-password" type="password" autocomplete="${signup ? 'new-password':'current-password'}" ${signup ? 'minlength="8"':''} required>${signup ? '<p class="fine">Use at least 8 characters.</p>':''}</div><button class="primary" data-testid="${prefix}-submit">${signup ? 'Create account':'Sign in'}</button></form><div id="auth-feedback"></div><p class="fine">${signup ? 'Already part of the table? <a href="/login">Sign in</a>' : 'New here? <a href="/signup">Create an account</a>'}</p></section></div>`;
  $('auth').onsubmit = async e => {
    e.preventDefault(); const button = $('auth').querySelector('button'); button.disabled = true; $('auth-feedback').innerHTML = '';
    try { session = await api('/auth/'+prefix,{method:'POST',body:JSON.stringify({email:$('email').value,password:$('password').value,...(signup ? {display_name:$('name').value}:{})})}); localStorage.setItem('tablekeeper-session',JSON.stringify(session)); location.href = '/'; }
    catch(error) { status('auth-feedback','auth-error',error.code === 'unauthenticated' ? 'That email and password did not match. Please try again.' : error.message); button.disabled = false; }
  };
}
function lookup() {
  $('app').innerHTML = `<div class="lookup-layout"><section class="intro"><div class="eyebrow">Your next good evening</div><h1>Plans, kept.</h1><p>Enter your confirmation reference to view or cancel your reservation.</p></section><form id="lookup" class="card lookup-form"><div><label for="reference">Confirmation reference</label><input id="reference" data-testid="lookup-reference-input" autocomplete="off" spellcheck="false" required></div><button class="primary" data-testid="lookup-submit">Find reservation</button></form><div id="lookup-feedback"></div><div id="detail"></div></div>`;
  let lookupVersion = 0;
  async function show(reference) {
    const version = ++lookupVersion; $('detail').innerHTML = ''; $('lookup-feedback').innerHTML = '<div class="loading" role="status">Finding your reservation…</div>';
    try {
      const reservation = await api('/reservations/'+encodeURIComponent(reference));
      const r = await api('/restaurants/'+encodeURIComponent(reservation.restaurant_id));
      if (version !== lookupVersion) return;
      $('lookup-feedback').innerHTML = '';
      $('detail').innerHTML = `<section class="card" style="margin-top:24px" data-testid="reservation-detail"><div class="detail-head"><h2>${esc(r.name)}</h2><span class="badge ${reservation.status}" data-testid="reservation-status">${esc(reservation.status)}</span></div><dl class="detail-list"><div><dt>Reference</dt><dd>${esc(reservation.reference)}</dd></div><div><dt>Date & local time</dt><dd>${esc(reservation.starts_at_local.replace('T',' · '))}</dd></div><div><dt>Your seating</dt><dd data-testid="reservation-tables">${esc(labels(r,idsOf(reservation)))}</dd></div><div><dt>Guests</dt><dd>${reservation.party_size}</dd></div></dl>${reservation.status === 'confirmed' ? '<button class="secondary cancel" id="cancel" data-testid="reservation-cancel-button">Cancel reservation</button>' : '<p class="fine">This reservation is cancelled. You can find another table whenever you’re ready.</p>'}</section>`;
      if ($('cancel')) $('cancel').onclick = async () => { const button = $('cancel'); button.disabled = true; try { await api('/reservations/'+encodeURIComponent(reference)+'/cancel',{method:'POST',body:'{}'}); await show(reference); } catch(e) { status('lookup-feedback','reservation-error',e.code === 'cutoff_passed' ? 'This reservation is too close to its start time to cancel.' : e.message); button.disabled = false; } };
    } catch(e) { if (version === lookupVersion) status('lookup-feedback','reservation-error',e.code === 'unauthenticated' ? 'Please sign in to view your reservation.' : e.code === 'not_found' ? 'We could not find that reservation for your account. Check the reference and try again.' : e.message); }
  }
  $('lookup').onsubmit = e => { e.preventDefault(); show($('reference').value.trim()); };
  const reference = new URLSearchParams(location.search).get('reference'); if (reference) { $('reference').value = reference; show(reference); }
}
if (route === '/signup') auth(true); else if (route === '/login') auth(false); else if (route === '/lookup') lookup(); else home();
