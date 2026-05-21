let currentUser = null;

const STATUS_OPTIONS = ['接体中', '冷藏中', '待告别', '已火化', '已安葬'];
const STATUS_COLORS = {
    '接体中': 'bg-blue-50 text-blue-700',
    '冷藏中': 'bg-indigo-50 text-indigo-700',
    '待告别': 'bg-yellow-50 text-yellow-700',
    '已火化': 'bg-orange-50 text-orange-700',
    '已安葬': 'bg-green-50 text-green-700',
};

function route() {
    const hash = window.location.hash.slice(1) || 'login';
    const app = document.getElementById('app');

    if (!currentUser && hash !== 'login') {
        window.location.hash = 'login';
        return;
    }

    if (hash === 'login') {
        renderLogin();
    } else {
        renderDeceasedList();
    }
}

function renderLogin() {
    document.getElementById('app').innerHTML = `
        <div class="min-h-screen flex items-center justify-center bg-gray-100">
            <div class="bg-white rounded-lg shadow p-8 w-full max-w-md">
                <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">殡葬CRM系统</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                        <input type="text" id="login-username" placeholder="admin" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
                        <input type="password" id="login-password" placeholder="admin123" />
                    </div>
                    <button onclick="doLogin()" class="btn-primary w-full">登录</button>
                </div>
                <div class="mt-4 text-center text-xs text-gray-400">
                    默认账号：admin / admin123
                </div>
            </div>
        </div>
    `;
}

async function doLogin() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    try {
        const res = await apiClient.login(username, password);
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('user', JSON.stringify(res.user));
        currentUser = res.user;
        window.location.hash = '';
    } catch (e) {
        alert('登录失败：' + e.message);
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    currentUser = null;
    window.location.hash = 'login';
}

async function renderDeceasedList() {
    let search = '';
    let list = [];

    const refresh = async () => {
        const params = search ? `search=${encodeURIComponent(search)}` : '';
        list = await apiClient.listDeceased(params).catch(() => []);
        render();
    };

    const render = () => {
        document.getElementById('app').innerHTML = `
            <nav class="bg-slate-800 text-white shadow">
                <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
                    <span class="text-xl font-bold">殡葬CRM</span>
                    <div class="flex items-center gap-4 text-sm">
                        <span>${currentUser?.real_name || ''}</span>
                        <button onclick="logout()" class="text-slate-300 hover:text-white">退出</button>
                    </div>
                </div>
            </nav>
            <div class="max-w-7xl mx-auto px-4 py-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold text-gray-800">逝者档案管理</h2>
                    <button onclick="showForm()" class="btn-primary text-sm">+ 新增档案</button>
                </div>
                <div class="mb-4 flex gap-2">
                    <input type="text" id="search-input" placeholder="搜索逝者姓名..." class="w-64" value="${search}" onchange="window.doSearch(this.value)" />
                    <button onclick="window.doSearch(document.getElementById('search-input').value)" class="btn-secondary text-sm">搜索</button>
                </div>
                <div class="bg-white rounded-lg shadow overflow-hidden">
                    <table class="min-w-full text-sm">
                        <thead class="bg-gray-50 text-gray-600">
                            <tr>
                                <th class="px-4 py-3 text-left">姓名</th>
                                <th class="px-4 py-3 text-left">性别</th>
                                <th class="px-4 py-3 text-left">年龄</th>
                                <th class="px-4 py-3 text-left">死亡时间</th>
                                <th class="px-4 py-3 text-left">冷藏编号</th>
                                <th class="px-4 py-3 text-left">家属联系人</th>
                                <th class="px-4 py-3 text-left">状态</th>
                                <th class="px-4 py-3 text-right">操作</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            ${list.length ? list.map(d => `
                                <tr class="hover:bg-gray-50">
                                    <td class="px-4 py-3 font-medium">${d.name}</td>
                                    <td class="px-4 py-3">${d.gender || '-'}</td>
                                    <td class="px-4 py-3">${d.age || '-'}</td>
                                    <td class="px-4 py-3">${d.death_time || '-'}</td>
                                    <td class="px-4 py-3">${d.refrigeration_no || '-'}</td>
                                    <td class="px-4 py-3">${d.family_name || '-'} ${d.family_phone || ''}</td>
                                    <td class="px-4 py-3"><span class="px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[d.status] || 'bg-gray-100'}">${d.status}</span></td>
                                    <td class="px-4 py-3 text-right">
                                        <button onclick="showForm(${d.id})" class="text-blue-600 hover:underline text-xs mr-2">编辑</button>
                                        <button onclick="deleteDeceased(${d.id})" class="text-red-500 hover:underline text-xs">删除</button>
                                    </td>
                                </tr>
                            `).join('') : '<tr><td colspan="8" class="px-4 py-8 text-center text-gray-400">暂无记录</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="modal-overlay" class="fixed inset-0 bg-black/50 hidden items-center justify-center z-50">
                <div id="modal-content" class="bg-white rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto mx-4"></div>
            </div>
        `;
        window.doSearch = (val) => { search = val; refresh(); };
    };

    refresh();
}

async function showForm(id = null) {
    let data = {};
    if (id) {
        try { data = await apiClient.getDeceased(id); } catch (e) { alert(e.message); return; }
    }

    const overlay = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');

    content.innerHTML = `
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold">${id ? '编辑档案' : '新增档案'}</h3>
                <button onclick="closeForm()" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div class="grid md:grid-cols-2 gap-4">
                <div><label class="block text-xs text-gray-500 mb-1">逝者姓名 *</label><input id="d-name" value="${data.name || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">性别</label>
                    <select id="d-gender">
                        <option value="">请选择</option>
                        <option value="男" ${data.gender === '男' ? 'selected' : ''}>男</option>
                        <option value="女" ${data.gender === '女' ? 'selected' : ''}>女</option>
                    </select>
                </div>
                <div><label class="block text-xs text-gray-500 mb-1">年龄</label><input type="number" id="d-age" value="${data.age || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">身份证号</label><input id="d-idcard" value="${data.id_card || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">死亡时间</label><input type="datetime-local" id="d-death-time" value="${data.death_time || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">死亡地点</label><input id="d-death-loc" value="${data.death_location || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">接体时间</label><input type="datetime-local" id="d-pickup-time" value="${data.pickup_time || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">冷藏编号</label><input id="d-ref-no" value="${data.refrigeration_no || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">家属姓名</label><input id="d-family-name" value="${data.family_name || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">家属电话</label><input id="d-family-phone" value="${data.family_phone || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">死亡证明编号</label><input id="d-cert-no" value="${data.death_cert_no || ''}" /></div>
                <div><label class="block text-xs text-gray-500 mb-1">当前状态</label>
                    <select id="d-status">
                        ${STATUS_OPTIONS.map(s => `<option value="${s}" ${data.status === s ? 'selected' : ''}>${s}</option>`).join('')}
                    </select>
                </div>
                <div class="md:col-span-2"><label class="block text-xs text-gray-500 mb-1">备注</label><textarea id="d-remark" rows="2">${data.remark || ''}</textarea></div>
            </div>
            <div class="flex gap-2 mt-4">
                <button onclick="saveDeceased(${id || 'null'})" class="btn-primary">保存</button>
                <button onclick="closeForm()" class="btn-secondary">取消</button>
            </div>
        </div>
    `;
}

function closeForm() {
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
}

async function saveDeceased(id) {
    const data = {
        name: document.getElementById('d-name').value,
        gender: document.getElementById('d-gender').value,
        age: parseInt(document.getElementById('d-age').value) || null,
        id_card: document.getElementById('d-idcard').value,
        death_time: document.getElementById('d-death-time').value,
        death_location: document.getElementById('d-death-loc').value,
        pickup_time: document.getElementById('d-pickup-time').value,
        refrigeration_no: document.getElementById('d-ref-no').value,
        family_name: document.getElementById('d-family-name').value,
        family_phone: document.getElementById('d-family-phone').value,
        death_cert_no: document.getElementById('d-cert-no').value,
        status: document.getElementById('d-status').value,
        remark: document.getElementById('d-remark').value,
    };
    if (!data.name) { alert('请填写逝者姓名'); return; }
    try {
        if (id) {
            await apiClient.updateDeceased(id, data);
        } else {
            await apiClient.createDeceased(data);
        }
        closeForm();
        window.location.reload();
    } catch (e) { alert(e.message); }
}

async function deleteDeceased(id) {
    if (!confirm('确定删除该档案？')) return;
    try {
        await apiClient.deleteDeceased(id);
        window.location.reload();
    } catch (e) { alert(e.message); }
}

async function init() {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        try {
            const me = await apiClient.me();
            currentUser = me;
        } catch (e) {
            currentUser = null;
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        }
    }
    route();
    window.addEventListener('hashchange', route);
}

init();
