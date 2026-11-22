/* Dashboard logic – plain JavaScript, Bootstrap 5 + Plotly */
const $ = s => document.querySelector(s);
const token = localStorage.getItem('token');
if (!token) location.href = '/';
let me = null, period = 'weekly', reminders = [];

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const when = s => new Date(/Z|[+-]\d\d:\d\d$/.test(s) ? s : s + 'Z');
const fmt = s => when(s).toLocaleString([], { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

function toast(text, bad) {
  const d = document.createElement('div'); d.className = 'toast-x' + (bad ? ' bad' : ''); d.textContent = text;
  $('#toasts').append(d); setTimeout(() => d.remove(), 4500);
}
async function api(path, opts = {}) {
  const headers = { Authorization: 'Bearer ' + token, ...(opts.json ? { 'Content-Type': 'application/json' } : {}) };
  const r = await fetch('/api' + path, { method: opts.method || 'GET', headers, body: opts.json ? JSON.stringify(opts.json) : undefined });
  if (r.status === 401) { localStorage.removeItem('token'); location.href = '/'; throw new Error('Signed out'); }
  if (!r.ok) {
    let d = {}; try { d = await r.json(); } catch { }
    const m = Array.isArray(d.detail) ? d.detail.map(x => x.msg.replace('Value error, ', '')).join(' ') : d.detail;
    throw new Error(m || 'Request failed');
  }
  return r.status === 204 ? null : (r.headers.get('content-type') || '').includes('json') ? r.json() : r;
}

/* ---------- tabs ---------- */
document.querySelectorAll('#nav [data-tab]').forEach(b => b.onclick = () => showTab(b.dataset.tab));
function showTab(name) {
  document.querySelectorAll('#nav [data-tab]').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-pane-x').forEach(p => p.classList.toggle('show', p.id === 'tab-' + name));
  ({ overview: loadOverview, add: loadRecords, alerts: loadAlerts, profile: fillProfile, admin: loadAdmin })[name]?.();
  if (name === 'overview') setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
}
$('#logout').onclick = () => { localStorage.removeItem('token'); location.href = '/'; };

/* ---------- overview ---------- */
const META = {
  systolic: { label: 'Systolic', unit: 'mmHg' }, diastolic: { label: 'Diastolic', unit: 'mmHg' }, glucose: { label: 'Glucose', unit: 'mg/dL' },
  weight_kg: { label: 'Weight', unit: 'kg' }, sleep_hours: { label: 'Sleep', unit: 'h' }, exercise_minutes: { label: 'Exercise', unit: 'min' },
  stress_level: { label: 'Stress', unit: '/10' }
};
const CHARTS = [
  { title: 'Blood pressure (mmHg)', keys: ['systolic', 'diastolic'], colors: ['#C8453F', '#2B6CB0'] },
  { title: 'Glucose (mg/dL)', keys: ['glucose'], colors: ['#B97A0B'] },
  { title: 'Weight (kg)', keys: ['weight_kg'], colors: ['#0E7C7B'] },
  { title: 'Sleep (hours)', keys: ['sleep_hours'], colors: ['#5B4B9A'] },
  { title: 'Exercise (minutes)', keys: ['exercise_minutes'], colors: ['#2F855A'], bar: true },
  { title: 'Stress (1–10)', keys: ['stress_level'], colors: ['#C05621'] },
];
document.querySelectorAll('#periodGroup [data-p]').forEach(b => b.onclick = () => {
  period = b.dataset.p;
  document.querySelectorAll('#periodGroup [data-p]').forEach(x => x.classList.toggle('active', x === b));
  loadOverview();
});

async function loadOverview() {
  const d = await api('/dashboard?period=' + period);
  const m = d.summary.metrics;
  const cells = Object.keys(META).filter(k => m[k]).map(k => {
    const v = m[k];
    return `<div class="cell"><div class="label">${META[k].label}</div>
      <div><span class="value">${v.latest}</span><span class="unit">${META[k].unit}</span></div>
      <div class="trend"><span class="dot ${v.trend.replace(' ', '-')}"></span>avg ${v.mean} · ${v.trend}</div></div>`;
  });
  if (d.bmi) cells.push(`<div class="cell"><div class="label">BMI</div><div><span class="value">${d.bmi}</span></div><div class="trend">from latest weight</div></div>`);
  $('#ledger').innerHTML = cells.join('') || `<div class="empty w-100" style="grid-column:1/-1">No readings in this period. Use “Add reading” to record your first measurement.</div>`;

  const box = $('#charts'); box.innerHTML = '';
  CHARTS.filter(c => c.keys.some(k => d.series[k])).forEach((c, i) => {
    const col = document.createElement('div'); col.className = 'col-lg-6';
    col.innerHTML = `<div class="panel"><h2>${c.title}</h2><div class="chart" id="ch${i}"></div></div>`;
    box.append(col);
    const traces = c.keys.filter(k => d.series[k]).map((k, j) => ({
      x: d.series[k].x, y: d.series[k].y, name: META[k].label, type: c.bar ? 'bar' : 'scatter',
      mode: 'lines+markers', line: { color: c.colors[j], width: 2.5 }, marker: { color: c.colors[j] }
    }));
    Plotly.newPlot('ch' + i, traces, {
      margin: { l: 40, r: 10, t: 10, b: 36 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: 'Plus Jakarta Sans', color: '#14282E' }, legend: { orientation: 'h', y: -0.25 }, xaxis: { gridcolor: '#E3EAF2' }, yaxis: { gridcolor: '#E3EAF2' }
    },
      { displayModeBar: false, responsive: true });
  });
  setBadge(d.unread_alerts);

  const r = await api('/risk/diabetes');
  $('#riskBox').innerHTML = r.available
    ? `<h2>Diabetes-risk estimate</h2><p class="mb-1"><span class="dot ${r.band === 'high' ? 'rising' : r.band === 'moderate' ? '' : 'stable'}" style="${r.band === 'moderate' ? 'background:var(--amber)' : ''}"></span>
       Estimated level: <b>${r.band}</b> (${Math.round(r.probability * 100)}%)</p><p class="small text-secondary mb-0">Model estimate based on glucose, diastolic BP, BMI and age. ${esc(r.disclaimer)}</p>`
    : `<h2>Diabetes-risk estimate</h2><p class="mb-0 text-secondary">${esc(r.reason)}</p>`;
}
function setBadge(n) { const b = $('#alertBadge'); b.textContent = n; b.classList.toggle('d-none', !n); }

/* ---------- add reading ---------- */
const FIELDS = ['systolic', 'diastolic', 'glucose', 'weight_kg', 'sleep_hours', 'exercise_minutes', 'stress_level'];
$('#recForm').onsubmit = async e => {
  e.preventDefault();
  const body = { notes: $('#f_notes').value || null };
  FIELDS.forEach(f => { const v = $('#f_' + f).value; body[f] = v === '' ? null : Number(v); });
  try {
    const res = await api('/records', { method: 'POST', json: body });
    toast('Reading saved'); e.target.reset();
    $('#recAlerts').innerHTML = res.alerts.map(a => `<div class="alert-item sev-${a.severity}">${esc(a.message)}</div>`).join('');
    loadRecords(); refreshBadge();
  } catch (err) { toast(err.message, true); }
};
async function loadRecords() {
  const recs = await api('/records?limit=15');
  $('#recTable').innerHTML = `<thead><tr><th>Date</th><th>BP</th><th>Glucose</th><th>Weight</th><th>Sleep</th><th>Exercise</th><th>Stress</th><th></th></tr></thead><tbody>` +
    (recs.map(r => `<tr><td>${fmt(r.recorded_at)}</td><td>${r.systolic ? r.systolic + '/' + r.diastolic : '–'}</td><td>${r.glucose ?? '–'}</td><td>${r.weight_kg ?? '–'}</td>
      <td>${r.sleep_hours ?? '–'}</td><td>${r.exercise_minutes ?? '–'}</td><td>${r.stress_level ?? '–'}</td>
      <td><button class="btn btn-sm btn-link text-danger" data-del="${r.id}">Delete</button></td></tr>`).join('') || `<tr><td colspan="8" class="empty">No readings yet.</td></tr>`) + '</tbody>';
  document.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => {
    if (!confirm('Delete this reading?')) return;
    await api('/records/' + b.dataset.del, { method: 'DELETE' }); toast('Reading deleted'); loadRecords();
  });
}
async function refreshBadge() { const d = await api('/alerts'); setBadge(d.filter(a => !a.is_read).length); }

/* ---------- assistant ---------- */
$('#chatForm').onsubmit = async e => {
  e.preventDefault();
  const input = $('#chatInput'), text = input.value.trim(); if (!text) return;
  input.value = ''; addMsg(text, 'user');
  const wait = addMsg('Thinking…', 'bot');
  try {
    const r = await api('/assistant/chat', { method: 'POST', json: { message: text } });
    wait.textContent = r.reply;
    $('#modeLabel').textContent = r.mode === 'agents' ? '· AI agents active' : '· offline demo mode (no API key set)';
  } catch (err) { wait.textContent = err.message; }
};
function addMsg(t, who) { const d = document.createElement('div'); d.className = 'msg ' + who; d.textContent = t; $('#chat').append(d); d.scrollIntoView({ block: 'end' }); return d; }

/* ---------- alerts & reminders ---------- */
async function loadAlerts() {
  const al = await api('/alerts');
  $('#alertList').innerHTML = al.map(a => `<div class="alert-item sev-${a.severity}" style="${a.is_read ? 'opacity:.6' : ''}">
    <div class="small text-secondary">${fmt(a.created_at)} · ${a.severity}</div>${esc(a.message)}</div>`).join('') || '<div class="empty">No alerts. Nothing has crossed a configured threshold.</div>';
  setBadge(al.filter(a => !a.is_read).length);
  reminders = await api('/reminders');
  $('#remList').innerHTML = reminders.map(r => `<div class="alert-item d-flex justify-content-between align-items-center">
    <div><b>${r.time_of_day}</b> ${esc(r.title)} <span class="small text-secondary">(${r.frequency})</span>${r.active ? '' : ' <span class="badge text-bg-secondary">paused</span>'}</div>
    <div><button class="btn btn-sm btn-link" data-tg="${r.id}">${r.active ? 'Pause' : 'Resume'}</button><button class="btn btn-sm btn-link text-danger" data-rd="${r.id}">Delete</button></div></div>`).join('') || '<div class="empty">No reminders yet.</div>';
  document.querySelectorAll('[data-tg]').forEach(b => b.onclick = async () => { await api(`/reminders/${b.dataset.tg}/toggle`, { method: 'PATCH' }); loadAlerts(); });
  document.querySelectorAll('[data-rd]').forEach(b => b.onclick = async () => { await api('/reminders/' + b.dataset.rd, { method: 'DELETE' }); loadAlerts(); });
}
$('#readAll').onclick = async () => { await api('/alerts/read-all', { method: 'POST' }); loadAlerts(); };
$('#remForm').onsubmit = async e => {
  e.preventDefault();
  try {
    await api('/reminders', { method: 'POST', json: { title: $('#remTitle').value, time_of_day: $('#remTime').value, frequency: $('#remFreq').value } });
    e.target.reset(); $('#remTime').value = '08:00'; toast('Reminder added'); loadAlerts();
  } catch (err) { toast(err.message, true); }
};
// Browser notifications while the page is open (only with the user's consent)
let lastFired = '';
setInterval(async () => {
  if (!me || !me.notifications_consent) return;
  const now = new Date(), hhmm = now.toTimeString().slice(0, 5), key = now.toDateString() + hhmm;
  if (key === lastFired) return;
  const due = reminders.filter(r => r.active && r.time_of_day === hhmm && (r.frequency === 'daily' || now.getDay() === 1));
  if (!due.length) return;
  lastFired = key;
  due.forEach(r => { toast('Reminder: ' + r.title); if (window.Notification && Notification.permission === 'granted') new Notification('Health reminder', { body: r.title }); });
}, 20000);

/* ---------- report ---------- */
$('#repBtn').onclick = async () => {
  try {
    const r = await api('/reports/pdf?days=' + $('#repDays').value);
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement('a'); a.href = url; a.download = `health_report_${$('#repDays').value}d.pdf`; a.click(); URL.revokeObjectURL(url);
  } catch (err) { toast(err.message, true); }
};

/* ---------- profile ---------- */
function fillProfile() {
  $('#p_name').value = me.full_name; $('#p_dob').value = me.date_of_birth || ''; $('#p_height').value = me.height_cm || '';
  $('#p_gender').value = me.gender || ''; $('#p_goal').value = me.health_goal || ''; $('#p_consent').checked = me.notifications_consent;
}
$('#profForm').onsubmit = async e => {
  e.preventDefault();
  try {
    me = await api('/auth/me', {
      method: 'PUT', json: {
        full_name: $('#p_name').value, date_of_birth: $('#p_dob').value || null,
        height_cm: $('#p_height').value ? +$('#p_height').value : null, gender: $('#p_gender').value || null,
        health_goal: $('#p_goal').value || null, notifications_consent: $('#p_consent').checked
      }
    });
    if (me.notifications_consent && window.Notification && Notification.permission === 'default') Notification.requestPermission();
    $('#who').textContent = me.full_name; toast('Profile saved');
  } catch (err) { toast(err.message, true); }
};

/* ---------- admin ---------- */
async function loadAdmin() {
  const [s, users, logs] = await Promise.all([api('/admin/stats'), api('/admin/users'), api('/admin/logs?limit=30')]);
  const stat = (l, v) => `<div class="col-6 col-md"><div class="panel"><div class="small text-secondary">${l}</div><div class="display h3 mb-0">${v}</div></div></div>`;
  $('#adminStats').innerHTML = stat('Users', s.users) + stat('Active users', s.active_users) + stat('Records', s.records) + stat('Alerts', s.alerts) + stat('Critical alerts', s.critical_alerts);
  $('#userTable').innerHTML = '<thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead><tbody>' +
    users.map(u => `<tr><td>${esc(u.full_name)}</td><td>${esc(u.email)}</td><td>${u.role}</td><td>${u.is_active ? 'active' : 'deactivated'}</td>
      <td>${u.id === me.id ? '' : `<button class="btn btn-sm btn-outline-primary" data-act="${u.id}" data-on="${!u.is_active}">${u.is_active ? 'Deactivate' : 'Activate'}</button>`}</td></tr>`).join('') + '</tbody>';
  document.querySelectorAll('[data-act]').forEach(b => b.onclick = async () => {
    try { await api(`/admin/users/${b.dataset.act}/active?active=${b.dataset.on}`, { method: 'PATCH' }); loadAdmin(); } catch (err) { toast(err.message, true); }
  });
  $('#logTable').innerHTML = '<thead><tr><th>Time</th><th>User id</th><th>Action</th></tr></thead><tbody>' +
    logs.map(l => `<tr><td>${fmt(l.created_at)}</td><td>${l.user_id ?? ''}</td><td>${esc(l.action)}</td></tr>`).join('') + '</tbody>';
}

/* ---------- start ---------- */
(async () => {
  me = await api('/auth/me');
  $('#who').textContent = me.full_name;
  $('#hello').textContent = 'Hello, ' + me.full_name.split(' ')[0];
  if (me.role === 'admin') $('#adminTab').classList.remove('d-none');
  reminders = await api('/reminders');
  loadOverview();
})();
