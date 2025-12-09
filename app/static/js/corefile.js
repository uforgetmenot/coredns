const toastContainer = document.getElementById('toast-container');

function initCorefilePage() {
  attachListeners();
  loadAllData();
}

function attachListeners() {
  document.getElementById('btn-preview-corefile')?.addEventListener('click', refreshCorefilePreview);
  document.getElementById('btn-generate-corefile')?.addEventListener('click', generateCorefile);
  document.getElementById('btn-create-backup')?.addEventListener('click', createBackup);
  document.getElementById('btn-refresh-backups')?.addEventListener('click', loadBackups);
}

async function loadAllData() {
  await Promise.allSettled([
    refreshCorefilePreview(),
    loadBackups()
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

async function refreshCorefilePreview() {
  try {
    const payload = await fetchJson('/api/corefile/preview');
    const data = payload.data || {};
    document.getElementById('corefile-preview').textContent = data.content || '暂无内容';
    if (data.generated_at) {
      document.getElementById('corefile-generated-at').textContent = new Date(data.generated_at).toLocaleString();
    }
  } catch (error) {
    console.error('加载 Corefile 预览失败', error);
    showToast('Corefile 预览失败', 'error');
  }
}

async function generateCorefile() {
  try {
    const payload = await fetchJson('/api/corefile/generate', { method: 'POST' });
    showToast(payload.message || 'Corefile 已生成');
    await Promise.all([refreshCorefilePreview(), loadBackups()]);
  } catch (error) {
    console.error('生成 Corefile 失败', error);
    showToast('生成 Corefile 失败', 'error');
  }
}

async function createBackup() {
  try {
    const payload = await fetchJson('/api/corefile/backups', { method: 'POST' });
    showToast('备份已创建');
    await loadBackups();
  } catch (error) {
    console.error('创建备份失败', error);
    const errorMsg = error.message || '创建备份失败';
    showToast(errorMsg, 'error');
  }
}

async function loadBackups() {
  try {
    const payload = await fetchJson('/api/corefile/backups');
    const data = payload.data || { backups: [] };
    const body = document.getElementById('backups-body');
    if (!data.backups.length) {
      body.innerHTML = '<tr><td colspan="5" class="text-center">暂无备份</td></tr>';
      return;
    }
    body.innerHTML = data.backups
      .map((backup, index) => `
        <tr ${backup.is_latest ? 'class="bg-base-200"' : ''}>
          <td>
            ${backup.id}
            ${backup.is_latest ? '<span class="badge badge-sm badge-primary ml-2">最新</span>' : ''}
          </td>
          <td class="text-xs font-mono">${backup.filename}</td>
          <td>${formatBytes(backup.size)}</td>
          <td>${new Date(backup.created_at).toLocaleString('zh-CN')}</td>
          <td>
            <div class="flex gap-2">
              <button class="btn btn-ghost btn-xs" data-backup="restore" data-id="${backup.id}">恢复</button>
              <button class="btn btn-ghost btn-xs text-error" data-backup="delete" data-id="${backup.id}" ${backup.is_latest ? 'disabled title="不能删除最新备份"' : ''}>删除</button>
            </div>
          </td>
        </tr>
      `)
      .join('');

    body.querySelectorAll('button[data-backup]').forEach((btn) => {
      btn.addEventListener('click', () => handleBackupAction(btn.dataset.backup, btn.dataset.id));
    });
  } catch (error) {
    console.error('加载备份失败', error);
    showToast('加载备份失败', 'error');
  }
}

function formatBytes(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

async function handleBackupAction(action, id) {
  if (action === 'restore' && !confirm('确认将 Corefile 回滚到所选备份?')) return;
  if (action === 'delete' && !confirm('确认删除该备份?')) return;

  const url = action === 'restore' ? `/api/corefile/restore/${id}` : `/api/corefile/backups/${id}`;
  const method = action === 'restore' ? 'POST' : 'DELETE';
  try {
    await fetchJson(url, { method });
    showToast(action === 'restore' ? '备份已恢复' : '备份已删除');
    await Promise.all([loadBackups(), refreshCorefilePreview()]);
  } catch (error) {
    console.error('备份操作失败', error);
    showToast('备份操作失败', 'error');
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
  document.addEventListener('DOMContentLoaded', initCorefilePage);
} else {
  initCorefilePage();
}
