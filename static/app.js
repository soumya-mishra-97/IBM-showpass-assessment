/* Browser interface only. The Django services are authoritative for business logic. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const state = { token: null, events: [], promo: null };
  const currency = value => `₹${Number(value || 0).toFixed(2)}`;
  const escapeText = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

  function notify(text, kind = '') {
    const el = byId('apiMessage');
    el.className = `result-box ${kind}`;
    el.textContent = text;
  }
  function validationText(text, kind = '') {
    const el = byId('validationFeedback');
    el.className = `inline-note span-two ${kind}`;
    el.textContent = text;
  }
  function errorMessage(data, code) {
    if (typeof data?.detail === 'string') return data.detail;
    if (data?.detail) return JSON.stringify(data.detail);
    if (data) return JSON.stringify(data);
    return `HTTP ${code}`;
  }
  async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const response = await fetch(path, {...options, headers});
    let payload;
    try { payload = await response.json(); } catch { payload = null; }
    if (!response.ok) throw new Error(`${response.status}: ${errorMessage(payload, response.status)}`);
    return payload;
  }
  function currentEvent() {
    return state.events.find(e => String(e.id) === byId('eventSelect').value);
  }
  function currentSection() {
    return currentEvent()?.sections.find(s => String(s.id) === byId('sectionSelect').value);
  }
  function updateSections() {
    const e = currentEvent();
    const select = byId('sectionSelect');
    select.innerHTML = e ? e.sections.map(s => `<option value="${s.id}">${escapeText(s.name)} · ${currency(s.price)} · ${s.available} left</option>`).join('') : '<option value="">Select an event</option>';
    select.disabled = !e || !e.sections.length;
    state.promo = null;
    validationText('Promo validation does not consume a promo use.');
    updateEstimate();
  }
  function updateEstimate() {
    const s = currentSection();
    const q = Math.max(0, Number(byId('quantity').value || 0));
    const subtotal = Number(s?.price || 0) * q;
    const service = q * 12;
    const facility = q * 5;
    const processing = 3;
    let discount = 0;
    if (state.promo && state.promo.code === byId('promoCode').value.trim().toUpperCase()) {
      discount = state.promo.discount_type === 'percentage' ? subtotal * Number(state.promo.discount_value) / 100 : Number(state.promo.discount_value);
      if (state.promo.max_discount != null) discount = Math.min(discount, Number(state.promo.max_discount));
      discount = Math.max(0, Math.min(discount, subtotal));
    }
    byId('estimateSubtotal').textContent = currency(subtotal);
    byId('estimateService').textContent = currency(service);
    byId('estimateFacility').textContent = currency(facility);
    byId('estimateDiscount').textContent = `−${currency(discount)}`;
    byId('estimateTotal').textContent = currency(subtotal + service + facility + processing - discount);
    byId('createButton').disabled = !state.token || !s || q < 1 || q > 20;
  }
  async function loadEvents() {
    state.events = await api('/api/events/');
    const select = byId('eventSelect');
    select.innerHTML = state.events.map(e => `<option value="${e.id}">${escapeText(e.name)}</option>`).join('');
    select.disabled = !state.events.length;
    updateSections();
  }
  async function loadOrders() {
    const orders = await api('/api/orders/');
    byId('orderList').innerHTML = orders.length ? orders.map(o => `<div class="order-card"><div><strong>Order #${o.id} · ${escapeText(o.event_name)}</strong><small>${o.tickets.length} ticket(s) · ${escapeText(o.promo_code_text || 'No promo')} · ${new Date(o.created_at).toLocaleString()}</small></div><div class="amount">${currency(o.total_amount)}<small>Payment: ${escapeText(o.payment_status)}</small></div></div>`).join('') : '<div class="empty-state">No orders yet. Create your first order above.</div>';
  }
  byId('loginForm').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      const result = await api('/api/auth/login/', {method:'POST', body:JSON.stringify({username:byId('username').value, password:byId('password').value})});
      state.token = result.token;
      byId('authIndicator').className = 'auth-indicator ok';
      byId('authIndicator').textContent = `● ${result.username} connected`;
      byId('loginBox').classList.add('hidden');
      byId('validateButton').disabled = false;
      byId('refreshOrders').disabled = false;
      await loadEvents();
      await loadOrders();
      notify('Authenticated. Choose an event and try SAVE25, WRONGEVENT or another scenario.', 'success');
    } catch (error) { notify(`Login failed: ${error.message}`, 'error'); }
  });
  async function validatePromo() {
    const e = currentEvent();
    if (!e || !state.token) return;
    state.promo = null;
    updateEstimate();
    try {
      const result = await api('/api/promos/validate/', {method:'POST',body:JSON.stringify({code:byId('promoCode').value,event_id:e.id,quantity:Number(byId('quantity').value)})});
      state.promo = result;
      validationText(`✓ Valid: ${result.discount_type} ${result.discount_value}. Uses unchanged until order creation.`, 'success');
      notify(`HTTP 200 · ${result.message}`, 'success');
    } catch (error) {
      validationText(error.message, 'error');
      notify(error.message, 'error');
    }
    updateEstimate();
  }
  byId('validateButton').addEventListener('click', validatePromo);
  byId('eventSelect').addEventListener('change', updateSections);
  byId('sectionSelect').addEventListener('change', updateEstimate);
  byId('quantity').addEventListener('input', () => {state.promo = null; updateEstimate();});
  byId('promoCode').addEventListener('input', () => {state.promo = null; updateEstimate();});
  byId('orderForm').addEventListener('submit', async event => {
    event.preventDefault();
    const e = currentEvent(), s = currentSection();
    if (!e || !s || !state.token) return;
    try {
      const result = await api('/api/orders/', {method:'POST', body:JSON.stringify({event_id:e.id,sections:[{section_id:s.id, quantity:Number(byId('quantity').value)}], promo_code:byId('promoCode').value})});
      notify(`HTTP 201 · Order #${result.id} created. Discount ${currency(result.discount_amount)}; final total ${currency(result.total_amount)}. Payment is ${result.payment_status}, not charged.`, 'success');
      await loadEvents();
      await loadOrders();
    } catch (error) {notify(`Order rejected · ${error.message}`, 'error');}
  });
  byId('refreshOrders').addEventListener('click', async () => {try { await loadOrders(); notify('Order list refreshed.','success'); } catch(e) {notify(e.message,'error');}});
  byId('scenarioGrid').addEventListener('click', event => {
    const b = event.target.closest('[data-code]');
    if (!b) return;
    document.querySelectorAll('.scenario').forEach(x => x.classList.remove('selected'));
    b.classList.add('selected');
    byId('promoCode').value = b.dataset.code;
    byId('quantity').value = '2';
    state.promo = null;
    updateEstimate();
    validationText(`Scenario: ${b.querySelector('strong').textContent}. Press “Validate promo”.`);
    document.getElementById('playground').scrollIntoView({behavior:'smooth'});
  });
  byId('themeToggle').addEventListener('click', () => {
    document.body.classList.toggle('dark');
    byId('themeToggle').setAttribute('aria-pressed', String(document.body.classList.contains('dark')));
    byId('themeToggle').setAttribute('aria-label', document.body.classList.contains('dark') ? 'Switch to light mode' : 'Switch to dark mode');
  });
  document.querySelectorAll('.nav-link[href^="#"]').forEach(link => {
    link.addEventListener('click', () => {
      document.querySelectorAll('.nav-link').forEach(item => item.classList.remove('active'));
      link.classList.add('active');
    });
  });
  updateEstimate();
})();
