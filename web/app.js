// 状态配置
const STATUS_CONFIG = {
  'Pending': { label: '待处理', color: 'gray', icon: '⏳' },
  'Taizi': { label: '太子分拣', color: 'blue', icon: '📬' },
  'Zhongshu': { label: '中书省规划', color: 'purple', icon: '📝' },
  'Menxia': { label: '门下省审议', color: 'yellow', icon: '🔍' },
  'Assigned': { label: '尚书省派发', color: 'cyan', icon: '📮' },
  'Doing': { label: '执行部执行', color: 'indigo', icon: '⚙️' },
  'Review': { label: '尚书省汇总', color: 'pink', icon: '📊' },
  'Done': { label: '已完成', color: 'green', icon: '✅' },
  'Cancelled': { label: '已取消', color: 'red', icon: '❌' },
};

let allTasks = [];
let currentFilter = 'all';

// 加载任务
async function loadTasks() {
  try {
    const response = await fetch('data/tasks.json?t=' + Date.now());
    allTasks = await response.json();
    allTasks.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    renderStats();
    renderTasks();
  } catch (error) {
    console.error('加载失败:', error);
    document.getElementById('loading').innerHTML = '<p class="text-red-500">加载失败</p>';
  }
}

// 渲染统计
function renderStats() {
  const stats = {
    '总计': allTasks.length,
    '待处理': allTasks.filter(t => t.state === 'Pending').length,
    '进行中': allTasks.filter(t => ['Taizi','Zhongshu','Menxia','Assigned','Doing','Review'].includes(t.state)).length,
    '已完成': allTasks.filter(t => t.state === 'Done').length,
    '已取消': allTasks.filter(t => t.state === 'Cancelled').length,
  };

  const container = document.getElementById('statsGrid');
  container.innerHTML = '';
  Object.entries(stats).forEach(([name, count]) => {
    container.innerHTML += `
      <div class="bg-white rounded-lg shadow p-4 text-center hover:shadow-md transition">
        <div class="text-3xl font-bold text-red-600">${count}</div>
        <div class="text-gray-600 text-sm mt-1">${name}</div>
      </div>
    `;
  });
}

// 渲染任务列表
function renderTasks() {
  const container = document.getElementById('taskList');
  let tasks = allTasks;

  if (currentFilter === 'active') {
    tasks = tasks.filter(t => ['Taizi','Zhongshu','Menxia','Assigned','Doing','Review'].includes(t.state));
  } else if (currentFilter === 'done') {
    tasks = tasks.filter(t => t.state === 'Done');
  }

  const searchTerm = document.getElementById('searchBox').value.toLowerCase();
  if (searchTerm) {
    tasks = tasks.filter(t => t.title.toLowerCase().includes(searchTerm) || t.id.toLowerCase().includes(searchTerm));
  }

  container.innerHTML = '';
  
  if (tasks.length === 0) {
    document.getElementById('empty').classList.remove('hidden');
    return;
  }
  document.getElementById('empty').classList.add('hidden');

  tasks.forEach(task => {
    const config = STATUS_CONFIG[task.state] || STATUS_CONFIG['Pending'];
    const progressPercent = getProgressPercent(task.state);
    
    container.innerHTML += `
      <div class="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer" onclick="showTaskDetail('${task.id}')">
        <div class="p-5">
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <div class="flex items-center space-x-3">
                <span class="text-xs font-mono text-gray-500">${task.id}</span>
                <span class="status-badge status-${config.color.toLowerCase()}">${config.icon} ${config.label}</span>
              </div>
              <h3 class="text-lg font-semibold mt-2 text-gray-800">${escapeHtml(task.title)}</h3>
              ${task.now ? `<p class="text-gray-600 mt-2 text-sm">${escapeHtml(task.now)}</p>` : ''}
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-500">${formatDate(task.createdAt)}</div>
              ${task.reviewRound > 0 ? `<div class="text-xs text-yellow-600 mt-1">🔄 审议${task.reviewRound}轮</div>` : ''}
            </div>
          </div>
          
          <div class="mt-4">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>进度</span>
              <span>${progressPercent}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-gradient-to-r from-red-600 to-red-400 h-2 rounded-full transition-all" style="width: ${progressPercent}%"></div>
            </div>
          </div>

          <div class="mt-3 flex items-center text-xs text-gray-500">
            ${renderFlowPreview(task.flow_log || [])}
          </div>
        </div>
      </div>
    `;
  });

  document.getElementById('loading').classList.add('hidden');
}

function getProgressPercent(state) {
  const progress = {
    'Pending': 0, 'Taizi': 10, 'Zhongshu': 30, 'Menxia': 50,
    'Assigned': 60, 'Doing': 75, 'Review': 90, 'Done': 100, 'Cancelled': 0,
  };
  return progress[state] || 0;
}

function renderFlowPreview(flowLog) {
  if (!flowLog || flowLog.length === 0) return '<span>暂无流转记录</span>';
  const recent = flowLog.slice(-3);
  return recent.map(f => `<span>${f.to}</span>`).join(' → ');
}

function showTaskDetail(taskId) {
  const task = allTasks.find(t => t.id === taskId);
  if (!task) return;

  const config = STATUS_CONFIG[task.state] || {};
  
  document.getElementById('modalTitle').innerHTML = `
    <span class="text-sm font-mono">${task.id}</span>
    <span class="ml-3">${escapeHtml(task.title)}</span>
  `;

  const flowHtml = (task.flow_log || []).map(f => `
    <div class="flex items-start space-x-3 py-2 border-b">
      <div class="text-red-600 font-bold">${new Date(f.at).toLocaleString('zh-CN')}</div>
      <div class="flex-1">
        <div class="font-semibold">${f.from} → ${f.to}</div>
        <div class="text-gray-600 text-sm">${escapeHtml(f.remark || '')}</div>
      </div>
    </div>
  `).join('');

  const progressHtml = (task.progress_log || []).map(p => `
    <div class="flex items-start space-x-3 py-2 border-b">
      <div class="text-gray-500 text-sm">${new Date(p.at).toLocaleString('zh-CN')}</div>
      <div class="flex-1">
        <div class="text-gray-800">${escapeHtml(p.text || '')}</div>
        ${p.todos && p.todos.length ? `
          <div class="mt-1 space-x-2">
            ${p.todos.map(td => `
              <span class="text-xs ${td.status==='completed'?'text-green-600 line-through':td.status==='in-progress'?'text-blue-600':'text-gray-400'}">
                ${td.status==='completed'?'✅':td.status==='in-progress'?'🔄':'⬜'} ${escapeHtml(td.title)}
              </span>
            `).join('')}
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');

  document.getElementById('modalContent').innerHTML = `
    <div class="grid grid-cols-2 gap-6 mb-6">
      <div class="bg-gray-50 p-4 rounded-lg">
        <div class="text-sm text-gray-500">当前状态</div>
        <div class="text-2xl font-bold mt-1">${config.icon || ''} ${config.label || task.state}</div>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <div class="text-sm text-gray-500">负责部门</div>
        <div class="text-2xl font-bold mt-1">${task.org || '未知'}</div>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <div class="text-sm text-gray-500">创建时间</div>
        <div class="text-lg font-semibold mt-1">${formatDate(task.createdAt)}</div>
      </div>
      <div class="bg-gray-50 p-4 rounded-lg">
        <div class="text-sm text-gray-500">更新时间</div>
        <div class="text-lg font-semibold mt-1">${formatDate(task.updatedAt)}</div>
      </div>
    </div>

    ${task.now ? `
    <div class="mb-6">
      <h4 class="font-bold text-lg mb-2">📍 当前动态</h4>
      <div class="bg-blue-50 border-l-4 border-blue-500 p-4">
        <p class="text-gray-800">${escapeHtml(task.now)}</p>
      </div>
    </div>
    ` : ''}

    <div class="grid grid-cols-2 gap-6">
      <div>
        <h4 class="font-bold text-lg mb-2">📜 流转记录</h4>
        <div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
          ${flowHtml || '<p class="text-gray-500">无记录</p>'}
        </div>
      </div>
      <div>
        <h4 class="font-bold text-lg mb-2">📊 进展汇报</h4>
        <div class="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
          ${progressHtml || '<p class="text-gray-500">无记录</p>'}
        </div>
      </div>
    </div>

    ${task.output ? `
    <div class="mt-6">
      <h4 class="font-bold text-lg mb-2">📦 产出物</h4>
      <div class="bg-green-50 border-l-4 border-green-500 p-4">
        <p class="text-gray-800 whitespace-pre-wrap">${escapeHtml(task.output)}</p>
      </div>
    </div>
    ` : ''}
  `;

  document.getElementById('taskModal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('taskModal').classList.add('hidden');
}

function filterTasks(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.remove('bg-gray-800', 'text-white');
    btn.classList.add('bg-gray-200');
    if (btn.dataset.filter === filter) {
      btn.classList.remove('bg-gray-200');
      btn.classList.add('bg-gray-800', 'text-white');
    }
  });
  renderTasks();
}

function searchTasks() {
  renderTasks();
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  return new Date(isoStr).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  });
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  loadTasks();
  setInterval(loadTasks, 30000); // 每 30 秒自动刷新
});
