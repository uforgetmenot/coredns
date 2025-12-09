const state = {
  recordsPage: 1,
  recordsPageSize: 10,
  recordsPages: 1,
  records: [],
  zones: [],
  zoneSearch: '',
  filters: {
    zone: '',
    search: '',
    status: ''
  }
};

const recordForm = document.getElementById('record-form');
const recordsBody = document.getElementById('records-body');
const paginationLabel = document.getElementById('records-pagination');
const toastContainer = document.getElementById('toast-container');
const recordModalElement = document.getElementById('recordModal');
const zoneListElement = document.getElementById('zone-list');
const zoneSearchInput = document.getElementById('zone-search');
const zoneRefreshButton = document.getElementById('btn-clear-zone');
const filterZoneInput = document.getElementById('filter-zone');

let zoneSearchDebounce;

function escapeHtml(text = '') {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDescription(description) {
  if (!description) return '<span class="text-base-content/60">--</span>';
  const safe = escapeHtml(description);
  const display = description.length > 6 ? `${escapeHtml(description.slice(0, 6))}…` : safe;
  return `<span class="tooltip" data-tip="${safe}">${display}</span>`;
}

function initRecordsPage() {
  attachListeners();
  loadZones();
  loadRecords(true);
}

function attachListeners() {
  document.getElementById('btn-refresh-records')?.addEventListener('click', () => loadRecords(true));
  document.getElementById('btn-apply-filter')?.addEventListener('click', () => {
    state.filters.zone = (filterZoneInput?.value || '').trim();
    state.filters.search = document.getElementById('filter-search').value.trim();
    state.filters.status = document.getElementById('filter-status').value;
    state.recordsPage = 1;
    renderZones();
    loadRecords(true);
  });

  document.getElementById('btn-prev-page')?.addEventListener('click', () => {
    if (state.recordsPage > 1) {
      state.recordsPage -= 1;
      loadRecords();
    }
  });

  document.getElementById('btn-next-page')?.addEventListener('click', () => {
    if (state.recordsPage < state.recordsPages) {
      state.recordsPage += 1;
      loadRecords();
    }
  });

  document.getElementById('records-body')?.addEventListener('click', (event) => {
    const actionBtn = event.target.closest('[data-action]');
    if (!actionBtn) return;
    const recordId = Number(actionBtn.dataset.id);
    const action = actionBtn.dataset.action;
    const record = state.records.find((item) => item.id === recordId);
    if (!record) return;

    if (action === 'edit') {
      editRecord(record);
    } else if (action === 'delete') {
      deleteRecord(recordId);
    }
  });

  recordForm?.addEventListener('submit', submitRecordForm);

  zoneListElement?.addEventListener('click', (event) => {
    const zoneButton = event.target.closest('[data-zone]');
    if (!zoneButton) return;
    const zone = zoneButton.dataset.zone;
    applyZoneFilter(zone === state.filters.zone ? '' : zone);
  });

  zoneSearchInput?.addEventListener('input', (event) => {
    state.zoneSearch = event.target.value.trim();
    clearTimeout(zoneSearchDebounce);
    zoneSearchDebounce = setTimeout(() => loadZones(), 250);
  });

  zoneRefreshButton?.addEventListener('click', () => {
    if (zoneSearchInput) {
      state.zoneSearch = zoneSearchInput.value.trim();
    }
    loadZones();
    loadRecords(true);
  });
}

function applyZoneFilter(zoneValue) {
  state.filters.zone = zoneValue;
  if (filterZoneInput) filterZoneInput.value = zoneValue;
  state.recordsPage = 1;
  renderZones();
  loadRecords(true);
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

async function loadRecords(showToastMessage = false) {
  const params = new URLSearchParams({
    page: state.recordsPage,
    page_size: state.recordsPageSize,
    sort_by: 'created_at',
    order: 'desc'
  });

  if (state.filters.zone) params.append('zone', state.filters.zone);
  if (state.filters.search) params.append('search', state.filters.search);
  if (state.filters.status) params.append('status', state.filters.status);

  try {
    const payload = await fetchJson(`/api/records?${params.toString()}`);
    state.records = payload.data;
    const pagination = payload.pagination;
    state.recordsPages = pagination.pages || 1;

    renderRecords();
    paginationLabel.textContent = `第 ${pagination.page}/${state.recordsPages} 页,共 ${pagination.total} 条`;
    document.getElementById('btn-prev-page').disabled = pagination.page <= 1;
    document.getElementById('btn-next-page').disabled = pagination.page >= state.recordsPages;

    if (showToastMessage) showToast('记录列表已更新');
  } catch (error) {
    console.error('Failed to load records', error);
    showToast('加载记录失败', 'error');
  }
}

async function loadZones() {
  if (!zoneListElement) return;

  zoneListElement.innerHTML = '<div class="text-sm text-base-content/70">加载中...</div>';
  const params = new URLSearchParams();
  if (state.zoneSearch) params.append('search', state.zoneSearch);

  const query = params.toString();

  try {
    const payload = await fetchJson(`/api/records/zones${query ? `?${query}` : ''}`);
    state.zones = payload.data || [];
    renderZones();
  } catch (error) {
    console.error('Failed to load zones', error);
    zoneListElement.innerHTML = '<div class="text-sm text-error">加载 Zone 失败</div>';
  }
}

function renderRecords() {
  if (!recordsBody) return;
  recordsBody.innerHTML = '';
  if (!state.records.length) {
    recordsBody.innerHTML = '<tr><td colspan="7" class="text-center">暂无记录</td></tr>';
    return;
  }

  const rows = state.records
    .map((record) => {
      return `
        <tr>
          <td>${record.zone}</td>
          <td>${record.hostname}</td>
          <td><code>${record.ip_address}</code></td>
          <td>${record.record_type}</td>
          <td>${formatDescription(record.description)}</td>
          <td>
            <span class="badge ${record.status === 'active' ? 'badge-success' : record.status === 'inactive' ? 'badge-warning' : 'badge-neutral'}">${record.status}</span>
          </td>
          <td>
            <div class="flex gap-2">
              <button class="btn btn-ghost btn-xs" data-action="edit" data-id="${record.id}">编辑</button>
              <button class="btn btn-ghost btn-xs text-error" data-action="delete" data-id="${record.id}">删除</button>
            </div>
          </td>
        </tr>`;
    })
    .join('');
  recordsBody.innerHTML = rows;
}

function renderZones() {
  if (!zoneListElement) return;

  if (!state.zones.length) {
    zoneListElement.innerHTML = '<div class="text-sm text-base-content/70">暂无 Zone</div>';
    return;
  }

  const items = state.zones
    .map((zone) => {
      const isActive = zone.name === state.filters.zone;
      return `
        <button class="btn btn-sm justify-between w-full ${isActive ? 'btn-primary' : 'btn-ghost'}" data-zone="${zone.name}">
          <span class="truncate text-left">${zone.name}</span>
          <span class="badge ${isActive ? 'badge-outline' : 'badge-ghost'}">${zone.total_records}</span>
        </button>`;
    })
    .join('');

  zoneListElement.innerHTML = items;
}

function editRecord(record) {
  document.getElementById('modal-title').textContent = '编辑 DNS 记录';
  document.getElementById('record-id').value = record.id;
  document.getElementById('record-zone').value = record.zone;
  document.getElementById('record-hostname').value = record.hostname;
  document.getElementById('record-ip').value = record.ip_address;
  document.getElementById('record-type').value = record.record_type;
  document.getElementById('record-status').value = record.status;
  document.getElementById('record-description').value = record.description || '';
  recordModalElement.showModal();
}

function resetRecordForm() {
  if (!recordForm) return;
  document.getElementById('modal-title').textContent = '新增 DNS 记录';
  recordForm.reset();
  document.getElementById('record-id').value = '';
  document.getElementById('record-type').value = 'A';
  document.getElementById('record-status').value = 'active';
}

window.resetRecordForm = resetRecordForm;

async function submitRecordForm(event) {
  event.preventDefault();

  const recordId = document.getElementById('record-id').value;
  const payload = {
    zone: document.getElementById('record-zone').value.trim(),
    hostname: document.getElementById('record-hostname').value.trim(),
    ip_address: document.getElementById('record-ip').value.trim(),
    record_type: document.getElementById('record-type').value,
    status: document.getElementById('record-status').value,
    description: document.getElementById('record-description').value.trim() || null
  };

  const requestInit = {
    method: recordId ? 'PUT' : 'POST',
    body: JSON.stringify(payload)
  };
  const url = recordId ? `/api/records/${recordId}` : '/api/records';

  try {
    await fetchJson(url, requestInit);
    showToast(recordId ? '记录已更新' : '记录已创建');
    recordModalElement.close();
    resetRecordForm();
    await loadRecords();
  } catch (error) {
    console.error('保存记录失败', error);
    showToast('保存记录失败，请检查输入', 'error');
  }
}

async function deleteRecord(recordId) {
  if (!confirm('确认删除该记录?')) return;
  try {
    await fetchJson(`/api/records/${recordId}?mode=soft`, { method: 'DELETE' });
    showToast('记录已删除');
    await loadRecords();
  } catch (error) {
    console.error('删除记录失败', error);
    showToast('删除记录失败', 'error');
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

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initRecordsPage);
} else {
  initRecordsPage();
}
