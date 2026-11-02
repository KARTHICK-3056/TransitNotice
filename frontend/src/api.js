const API_BASE = '/api';
const DEMO_BASE = '/demo-source';

export async function fetchNotices(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'all') {
      query.append(k, v);
    }
  });
  const res = await fetch(`${API_BASE}/notices?${query.toString()}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchNoticeDetail(noticeId) {
  const res = await fetch(`${API_BASE}/notices/${encodeURIComponent(noticeId)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchAlertOptions() {
  const res = await fetch(`${API_BASE}/alerts/options`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function subscribeAlerts(email, preferences) {
  const res = await fetch(`${API_BASE}/alerts/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, ...preferences })
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchSources() {
  const res = await fetch(`${API_BASE}/sources`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function triggerAdminRefresh() {
  const res = await fetch(`${API_BASE}/admin/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Mentor Demo Mutations
export async function demoExtend24h(noticeId = 'METRO-DEMO-01') {
  const res = await fetch(`${DEMO_BASE}/metro/extend-24h`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notice_id: noticeId })
  });
  return res.json();
}

export async function demoInjectOpenEnded() {
  const res = await fetch(`${DEMO_BASE}/metro/inject-open-ended`, { method: 'POST' });
  return res.json();
}

export async function demoSimulate503() {
  const res = await fetch(`${DEMO_BASE}/metro/simulate-503`, { method: 'POST' });
  return res.json();
}

export async function demoRecover() {
  const res = await fetch(`${DEMO_BASE}/metro/recover`, { method: 'POST' });
  return res.json();
}

export async function demoReset() {
  const res = await fetch(`${DEMO_BASE}/metro/reset`, { method: 'POST' });
  return res.json();
}

