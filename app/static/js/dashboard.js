const toastContainer = document.getElementById('toast-container');
const upstreamForm = document.getElementById('upstream-dns-form');
const upstreamDefaults = {
  primary: upstreamForm?.dataset.defaultPrimary || '',
  secondary: upstreamForm?.dataset.defaultSecondary || ''
};

function initDashboard() {
  attachListeners();
  loadAllData();
}

function attachListeners() {
  document.getElementById('btn-reload-coredns')?.addEventListener('click', reloadCoreDNS);
  document.getElementById('upstream-dns-form')?.addEventListener('submit', handleUpstreamDNSSubmit);
}

async function loadAllData() {
  await Promise.allSettled([
    loadStats(),
    loadCoreDNSStatus(),
    loadUpstreamDNS()
  ]);
}

async function fetchJson(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Request failed');
  }
  if (response.status === 204) return null;
  return response.json();
}

async function loadStats() {
  try {
    const [total, active, inactive, zonesSample] = await Promise.all([
      fetchJson('/api/records?page=1&page_size=1&include_deleted=true'),
      fetchJson('/api/records?page=1&page_size=1&status=active'),
      fetchJson('/api/records?page=1&page_size=1&status=inactive'),
      fetchJson('/api/records?page=1&page_size=100')
    ]);

    document.getElementById('stat-total-records').textContent = total.pagination.total;
    document.getElementById('stat-active-records').textContent = active.pagination.total;
    document.getElementById('stat-inactive-records').textContent = inactive.pagination.total;

    const zones = new Set((zonesSample.data || []).map((record) => record.zone));
    document.getElementById('stat-zones').textContent = zones.size;
  } catch (error) {
    console.error('Failed to load stats', error);
  }
}

async function loadCoreDNSStatus() {
  try {
    const payload = await fetchJson('/api/coredns/status');
    const data = payload.data || {};
    const badge = document.getElementById('coredns-badge');
    badge.textContent = data.status;
    badge.className = `badge badge-lg ${data.running ? 'badge-success' : 'badge-error'}`;

    const details = document.getElementById('coredns-details');
    details.innerHTML = Object.entries(data)
      .map(([key, value]) => `<div class="font-semibold capitalize">${key}</div><div>${value}</div>`)
      .join('');
  } catch (error) {
    console.error('加载 CoreDNS 状态失败', error);
    showToast('CoreDNS 状态加载失败', 'error');
  }
}

async function reloadCoreDNS() {
  try {
    const payload = await fetchJson('/api/coredns/reload', { method: 'POST' });
    showToast(payload.message || 'CoreDNS 已重载');
    await loadCoreDNSStatus();
  } catch (error) {
    console.error('重载 CoreDNS 失败', error);
    showToast('重载 CoreDNS 失败', 'error');
  }
}

function showToast(message, type = 'success') {
  if (!toastContainer) return;
  const wrapper = document.createElement('div');
  wrapper.className = `alert ${type === 'error' ? 'alert-error' : 'alert-success'}`;
  wrapper.innerHTML = `<span>${message}</span>`;
  toastContainer.appendChild(wrapper);
  setTimeout(() => wrapper.remove(), 4000);
}

async function loadUpstreamDNS() {
  try {
    const payload = await fetchJson('/api/settings/upstream-dns');
    const data = payload.data || {};
    document.getElementById('primary-dns').value = data.primary_dns || upstreamDefaults.primary;
    document.getElementById('secondary-dns').value = data.secondary_dns || upstreamDefaults.secondary;
  } catch (error) {
    console.error('加载上级 DNS 配置失败', error);
    showToast('上级 DNS 配置加载失败', 'error');
  }
}

async function handleUpstreamDNSSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const primaryDNS = form.elements['primary_dns'].value.trim();
  const secondaryDNS = form.elements['secondary_dns'].value.trim();

  try {
    const payload = await fetchJson('/api/settings/upstream-dns', {
      method: 'PUT',
      body: JSON.stringify({
        primary_dns: primaryDNS,
        secondary_dns: secondaryDNS || null
      })
    });
    showToast(payload.message || '上级 DNS 配置已更新');
  } catch (error) {
    console.error('更新上级 DNS 配置失败', error);
    showToast('更新上级 DNS 配置失败', 'error');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboard);
} else {
  initDashboard();
}
