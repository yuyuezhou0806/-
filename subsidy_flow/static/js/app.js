// ===================== 全局状态 =====================
let currentUser = null;
let industries = [];

const STATUS_LABELS = {
    draft: '草稿',
    contract_signed: '已签合同',
    implementing: '实施中',
    audit_pending: '待审计',
    audit_done: '审计完成',
    acceptance_pending: '待验收',
    accepted: '已验收',
    subsidy_approved: '补贴已批',
    subsidy_paid: '补贴已发',
    rejected: '已驳回',
};

const STATUS_OPTIONS = [
    { value: 'contract_signed', label: '已签合同' },
    { value: 'implementing', label: '实施中' },
    { value: 'audit_pending', label: '待审计' },
    { value: 'audit_done', label: '审计完成' },
    { value: 'acceptance_pending', label: '待验收' },
    { value: 'accepted', label: '已验收' },
    { value: 'subsidy_approved', label: '补贴已批' },
    { value: 'subsidy_paid', label: '补贴已发' },
    { value: 'rejected', label: '驳回' },
];

const LEVEL_LABELS = {
    level_2: '二级',
    level_3: '三级',
    level_4: '四级',
};

const EXPENSE_CATEGORIES = [
    { value: 'software', label: '软件', subsidiable: true },
    { value: 'cloud_service', label: '云服务', subsidiable: true },
    { value: 'hardware_equipment', label: '硬件设备', subsidiable: true },
    { value: 'implementation_service', label: '实施服务', subsidiable: true },
    { value: 'gateway', label: '网关', subsidiable: true },
    { value: 'router', label: '路由', subsidiable: true },
    { value: 'sensor', label: '传感器', subsidiable: true },
    { value: 'ai_integrated_machine', label: '大模型一体机', subsidiable: true },
    { value: 'industrial_control_system', label: '工业控制系统', subsidiable: true },
    { value: 'firewall', label: '防火墙', subsidiable: true },
    { value: 'training', label: '培训费', subsidiable: false },
    { value: 'maintenance', label: '维保费', subsidiable: false },
    { value: 'consulting', label: '咨询费', subsidiable: false },
    { value: 'other', label: '其他', subsidiable: false },
];

// ===================== 路由 =====================
function route() {
    const hash = window.location.hash.slice(1) || 'landing';
    const [path, id] = hash.split('/');
    const app = document.getElementById('app');

    // 公开页面
    const publicPages = ['landing', 'calculator', 'compliance', 'policy', 'login'];
    if (publicPages.includes(path)) {
        renderPublicPage(path);
        return;
    }

    // 需要登录
    if (!currentUser) {
        window.location.hash = 'login';
        return;
    }

    switch (path) {
        case 'dashboard': renderDashboard(); break;
        case 'clients': renderClients(); break;
        case 'client': renderClientDetail(parseInt(id)); break;
        case 'projects': renderProjects(); break;
        case 'project': renderProjectDetail(parseInt(id)); break;
        case 'project-new': renderProjectNew(); break;
        case 'project-edit': renderProjectEdit(parseInt(id)); break;
        case 'project-expenses': renderProjectExpenses(parseInt(id)); break;
        default: renderLanding();
    }
}

// ===================== 布局 =====================
function renderPublicLayout(content) {
    const app = document.getElementById('app');
    app.innerHTML = `
        <nav class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
                <a href="#landing" class="text-xl font-bold text-blue-700">广州数字化补贴通</a>
                <div class="space-x-4 text-sm">
                    <a href="#landing" class="text-gray-600 hover:text-blue-600">首页</a>
                    <a href="#calculator" class="text-gray-600 hover:text-blue-600">补贴计算器</a>
                    <a href="#compliance" class="text-gray-600 hover:text-blue-600">合规校验</a>
                    <a href="#policy" class="text-gray-600 hover:text-blue-600">政策速览</a>
                    <a href="#login" class="text-blue-600 font-medium">工作人员登录</a>
                </div>
            </div>
        </nav>
        ${content}
    `;
}

function renderInternalLayout(content) {
    const app = document.getElementById('app');
    app.innerHTML = `
        <nav class="bg-blue-800 text-white shadow">
            <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
                <a href="#dashboard" class="text-xl font-bold">广州数字化补贴通 <span class="text-xs font-normal opacity-80">管理后台</span></a>
                <div class="flex items-center space-x-4 text-sm">
                    <a href="#dashboard" class="hover:text-blue-200">工作台</a>
                    <a href="#clients" class="hover:text-blue-200">客户</a>
                    <a href="#projects" class="hover:text-blue-200">项目</a>
                    <a href="#landing" target="_blank" class="hover:text-blue-200">获客页面</a>
                    <span class="opacity-70">|</span>
                    <span>${currentUser.real_name}</span>
                    <button onclick="logout()" class="text-blue-200 hover:text-white">退出</button>
                </div>
            </div>
        </nav>
        <div class="max-w-7xl mx-auto px-4 py-6">
            ${content}
        </div>
    `;
}

// ===================== 公开页面 =====================
async function renderPublicPage(page) {
    if (page === 'landing') {
        const countdown = await apiClient.deadlineCountdown().catch(() => ({ days_remaining: 0 }));
        renderPublicLayout(`
            <div class="bg-gradient-to-br from-blue-700 to-blue-900 text-white py-16">
                <div class="max-w-4xl mx-auto px-4 text-center">
                    <h1 class="text-4xl font-bold mb-4">广州市中小企业数字化转型补贴</h1>
                    <p class="text-xl opacity-90 mb-2">最高补贴 500 万元 · 8 大重点行业 · 政策截止 2026-12-31</p>
                    <div class="inline-block bg-white/20 backdrop-blur rounded-lg px-6 py-3 mt-4">
                        <span class="text-3xl font-bold">${countdown.days_remaining}</span>
                        <span class="text-sm opacity-90 ml-1">天剩余</span>
                    </div>
                </div>
            </div>
            <div class="max-w-5xl mx-auto px-4 py-12">
                <div class="grid md:grid-cols-3 gap-6">
                    <a href="#calculator" class="card-hover bg-white rounded-xl shadow p-8 text-center border border-gray-100">
                        <div class="text-4xl mb-4">🧮</div>
                        <h3 class="text-xl font-bold text-gray-800 mb-2">补贴计算器</h3>
                        <p class="text-gray-500 text-sm">输入数字化等级和投入金额，秒算你能拿多少补贴</p>
                        <div class="mt-4 text-blue-600 font-medium text-sm">立即测算 →</div>
                    </a>
                    <a href="#compliance" class="card-hover bg-white rounded-xl shadow p-8 text-center border border-gray-100">
                        <div class="text-4xl mb-4">✅</div>
                        <h3 class="text-xl font-bold text-gray-800 mb-2">合同合规校验</h3>
                        <p class="text-gray-500 text-sm">不同行业合同签订时间要求不同，一键校验是否合规</p>
                        <div class="mt-4 text-blue-600 font-medium text-sm">立即校验 →</div>
                    </a>
                    <a href="#policy" class="card-hover bg-white rounded-xl shadow p-8 text-center border border-gray-100">
                        <div class="text-4xl mb-4">📋</div>
                        <h3 class="text-xl font-bold text-gray-800 mb-2">政策速览</h3>
                        <p class="text-gray-500 text-sm">七大政策要点结构化解读，重点数字高亮展示</p>
                        <div class="mt-4 text-blue-600 font-medium text-sm">查看详情 →</div>
                    </a>
                </div>
                <div class="mt-12 bg-blue-50 rounded-xl p-8 text-center">
                    <h3 class="text-2xl font-bold text-blue-900 mb-3">不确定自己是否符合条件？</h3>
                    <p class="text-blue-700 mb-4">留下联系方式，专业申报顾问为您免费评估</p>
                    <div class="flex justify-center gap-4 text-sm text-blue-600">
                        <span>📞 咨询热线：400-XXX-XXXX</span>
                        <span>📍 服务范围：广州市 8 大试点行业</span>
                    </div>
                </div>
            </div>
        `);
    } else if (page === 'calculator') {
        renderCalculator();
    } else if (page === 'compliance') {
        renderCompliance();
    } else if (page === 'policy') {
        renderPolicySummary();
    } else if (page === 'login') {
        renderLogin();
    }
}

async function renderCalculator() {
    if (!industries.length) {
        industries = await apiClient.industries().catch(() => []);
    }
    renderPublicLayout(`
        <div class="max-w-2xl mx-auto px-4 py-12">
            <div class="bg-white rounded-xl shadow p-8">
                <h2 class="text-2xl font-bold mb-6 text-center">补贴计算器</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">数字化等级</label>
                        <select id="calc-level" class="w-full">
                            <option value="">请选择</option>
                            <option value="level_2">二级（上限 60 万）</option>
                            <option value="level_3">三级（上限 200 万）</option>
                            <option value="level_4">四级（上限 500 万）</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">预计数字化投入（元）</label>
                        <input type="number" id="calc-investment" class="w-full" placeholder="例如：1000000" />
                    </div>
                    <button onclick="runCalc()" class="btn-primary w-full text-lg py-3">立即测算</button>
                </div>
                <div id="calc-result" class="mt-6 hidden">
                    <!-- 结果动态插入 -->
                </div>
            </div>
        </div>
    `);
    window.runCalc = async () => {
        const level = document.getElementById('calc-level').value;
        const investment = parseFloat(document.getElementById('calc-investment').value);
        if (!level || !investment) {
            alert('请填写完整信息');
            return;
        }
        try {
            const res = await apiClient.calculate({ digital_level: level, total_investment: investment });
            const el = document.getElementById('calc-result');
            el.classList.remove('hidden');
            el.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div class="text-center">
                        <div class="text-sm text-green-700 mb-1">预估可获得补贴</div>
                        <div class="text-4xl font-bold text-green-800">${res.estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})} <span class="text-lg">元</span></div>
                    </div>
                    <div class="mt-4 grid grid-cols-2 gap-4 text-sm">
                        <div class="bg-white rounded p-3">
                            <div class="text-gray-500">补贴上限</div>
                            <div class="font-bold text-gray-800">${res.subsidy_cap.toLocaleString('zh-CN', {maximumFractionDigits: 0})} 元</div>
                        </div>
                        <div class="bg-white rounded p-3">
                            <div class="text-gray-500">补贴比例</div>
                            <div class="font-bold text-gray-800">${(res.max_subsidy_rate * 100).toFixed(0)}%</div>
                        </div>
                    </div>
                    <div class="mt-3 text-xs text-green-700 bg-green-100 rounded p-2">${res.note}</div>
                </div>
            `;
        } catch (e) {
            alert(e.message);
        }
    };
}

async function renderCompliance() {
    if (!industries.length) {
        industries = await apiClient.industries().catch(() => []);
    }
    renderPublicLayout(`
        <div class="max-w-2xl mx-auto px-4 py-12">
            <div class="bg-white rounded-xl shadow p-8">
                <h2 class="text-2xl font-bold mb-6 text-center">合同合规校验器</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">所属行业</label>
                        <select id="comp-industry" class="w-full">
                            <option value="">请选择</option>
                            ${industries.map(i => `<option value="${i.key}">${i.name}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">合同类型</label>
                        <select id="comp-type" class="w-full">
                            <option value="">请选择</option>
                            <option value="two_party">两方合同（企业与牵引单位）</option>
                            <option value="multi_party">多方合同（企业、牵引单位、服务商）</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">合同签订日期</label>
                        <input type="date" id="comp-date" class="w-full" />
                    </div>
                    <button onclick="runCompliance()" class="btn-primary w-full text-lg py-3">一键校验</button>
                </div>
                <div id="comp-result" class="mt-6 hidden">
                    <!-- 结果动态插入 -->
                </div>
            </div>
        </div>
    `);
    window.runCompliance = async () => {
        const industry = document.getElementById('comp-industry').value;
        const type = document.getElementById('comp-type').value;
        const date = document.getElementById('comp-date').value;
        if (!industry || !type || !date) {
            alert('请填写完整信息');
            return;
        }
        try {
            const res = await apiClient.checkCompliance({ industry, contract_type: type, sign_date: date });
            const el = document.getElementById('comp-result');
            el.classList.remove('hidden');
            const colorClass = res.compliant ? 'green' : 'red';
            const icon = res.compliant ? '✅' : '❌';
            el.innerHTML = `
                <div class="bg-${colorClass}-50 border border-${colorClass}-200 rounded-lg p-6">
                    <div class="text-center text-2xl mb-2">${icon}</div>
                    <div class="text-center text-xl font-bold text-${colorClass}-800 mb-4">
                        ${res.compliant ? '合规' : '不合规'}
                    </div>
                    <div class="space-y-2 text-sm">
                        ${res.reasons.map(r => `<div class="flex items-start gap-2"><span class="text-${colorClass}-600 mt-0.5">•</span><span>${r}</span></div>`).join('')}
                    </div>
                    ${res.warnings.length ? `
                        <div class="mt-3 bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
                            <div class="font-bold mb-1">⚠️ 预警</div>
                            ${res.warnings.map(w => `<div>• ${w}</div>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        } catch (e) {
            alert(e.message);
        }
    };
}

async function renderPolicySummary() {
    const data = await apiClient.policySummary().catch(() => []);
    renderPublicLayout(`
        <div class="max-w-3xl mx-auto px-4 py-12">
            <h2 class="text-2xl font-bold mb-6 text-center">政策速览</h2>
            <div class="space-y-4">
                ${data.map((item, idx) => `
                    <div class="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
                        <div class="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50" onclick="togglePolicy(${idx})">
                            <div class="flex items-center gap-3">
                                <span class="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded">${item.tag}</span>
                                <span class="font-bold text-gray-800">${item.title}</span>
                            </div>
                            <span id="policy-icon-${idx}" class="text-gray-400">▼</span>
                        </div>
                        <div id="policy-body-${idx}" class="px-4 pb-4 text-sm text-gray-600">
                            <p class="mb-2">${item.content}</p>
                            <span class="inline-block bg-red-50 text-red-700 font-bold px-2 py-1 rounded text-xs">${item.highlight}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `);
    window.togglePolicy = (idx) => {
        const body = document.getElementById(`policy-body-${idx}`);
        const icon = document.getElementById(`policy-icon-${idx}`);
        if (body.style.display === 'none') {
            body.style.display = 'block';
            icon.textContent = '▼';
        } else {
            body.style.display = 'none';
            icon.textContent = '▶';
        }
    };
}

function renderLogin() {
    renderPublicLayout(`
        <div class="max-w-md mx-auto px-4 py-16">
            <div class="bg-white rounded-xl shadow p-8">
                <h2 class="text-2xl font-bold mb-6 text-center">工作人员登录</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                        <input type="text" id="login-username" class="w-full" />
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
                        <input type="password" id="login-password" class="w-full" />
                    </div>
                    <button onclick="doLogin()" class="btn-primary w-full">登录</button>
                </div>
                <div class="mt-4 text-center text-xs text-gray-400">
                    默认账号：admin / admin123<br>agent / agent123
                </div>
            </div>
        </div>
    `);
    window.doLogin = async () => {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        try {
            const res = await apiClient.login(username, password);
            localStorage.setItem('token', res.access_token);
            localStorage.setItem('user', JSON.stringify(res.user));
            currentUser = res.user;
            window.location.hash = 'dashboard';
        } catch (e) {
            alert('登录失败：' + e.message);
        }
    };
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    currentUser = null;
    window.location.hash = 'landing';
}

// ===================== 内部页面 =====================
async function renderDashboard() {
    const stats = await apiClient.dashboard().catch(() => ({
        total_projects: 0, draft_count: 0, in_progress_count: 0,
        accepted_count: 0, subsidy_approved_count: 0,
        total_estimated_subsidy: 0, total_approved_subsidy: 0,
        days_remaining: 0, deadline: '2026-12-31'
    }));

    renderInternalLayout(`
        <div class="mb-6 bg-gradient-to-r from-red-600 to-orange-500 text-white rounded-xl p-4 flex items-center justify-between">
            <div>
                <div class="text-sm opacity-90">政策截止倒计时</div>
                <div class="text-2xl font-bold">${stats.deadline} 还剩 ${stats.days_remaining} 天</div>
            </div>
            <a href="#project-new" class="bg-white text-red-600 font-bold px-4 py-2 rounded-lg text-sm hover:bg-gray-100">+ 新建项目</a>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">项目总数</div>
                <div class="text-2xl font-bold text-gray-800">${stats.total_projects}</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">草稿/进行中</div>
                <div class="text-2xl font-bold text-blue-600">${stats.draft_count + stats.in_progress_count}</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">已验收</div>
                <div class="text-2xl font-bold text-teal-600">${stats.accepted_count}</div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
                <div class="text-sm text-gray-500">补贴已批</div>
                <div class="text-2xl font-bold text-green-600">${stats.subsidy_approved_count}</div>
            </div>
        </div>

        <div class="grid md:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="font-bold text-gray-800 mb-4">预估补贴总额</h3>
                <div class="text-3xl font-bold text-blue-700">¥ ${stats.total_estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</div>
                <div class="text-sm text-gray-400 mt-1">所有项目预估补贴合计</div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="font-bold text-gray-800 mb-4">已批准补贴总额</h3>
                <div class="text-3xl font-bold text-green-700">¥ ${stats.total_approved_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</div>
                <div class="text-sm text-gray-400 mt-1">已批复补贴合计</div>
            </div>
        </div>
    `);
}

async function renderClients() {
    let search = '';
    let clients = await apiClient.listClients().catch(() => []);

    const refresh = async () => {
        const params = search ? `search=${encodeURIComponent(search)}` : '';
        clients = await apiClient.listClients(params).catch(() => []);
        renderList();
    };

    const renderList = () => {
        const content = `
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">客户管理</h2>
                <a href="#client-new" onclick="renderClientNew(); return false;" class="btn-primary text-sm">+ 新增客户</a>
            </div>
            <div class="mb-4">
                <input type="text" id="client-search" placeholder="搜索企业名称..." class="w-full md:w-64"
                    value="${search}" onchange="window.clientSearch(this.value)" />
            </div>
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <table class="min-w-full text-sm">
                    <thead class="bg-gray-50 text-gray-600">
                        <tr>
                            <th class="px-4 py-3 text-left">企业名称</th>
                            <th class="px-4 py-3 text-left">行业</th>
                            <th class="px-4 py-3 text-left">联系人</th>
                            <th class="px-4 py-3 text-left">数字化等级</th>
                            <th class="px-4 py-3 text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        ${clients.length ? clients.map(c => `
                            <tr class="hover:bg-gray-50">
                                <td class="px-4 py-3 font-medium">${c.company_name}</td>
                                <td class="px-4 py-3">${_industryName(c.industry)}</td>
                                <td class="px-4 py-3">${c.contact_name || '-'} ${c.contact_phone || ''}</td>
                                <td class="px-4 py-3">${LEVEL_LABELS[c.digital_level] || '-'}</td>
                                <td class="px-4 py-3 text-right">
                                    <a href="#client/${c.id}" class="text-blue-600 hover:underline mr-2">详情</a>
                                </td>
                            </tr>
                        `).join('') : '<tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">暂无客户</td></tr>'}
                    </tbody>
                </table>
            </div>
        `;
        renderInternalLayout(content);
        window.clientSearch = (val) => { search = val; refresh(); };
        window.renderClientNew = () => {
            const formContent = `
                <div class="max-w-xl mx-auto">
                    <h2 class="text-xl font-bold mb-4">新增客户</h2>
                    <div class="bg-white rounded-lg shadow p-6 space-y-4">
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">企业名称 *</label><input id="c-name" class="w-full" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">联系人</label><input id="c-contact" class="w-full" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">联系电话</label><input id="c-phone" class="w-full" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">所属行业</label>
                            <select id="c-industry" class="w-full"><option value="">请选择</option>${industries.map(i => `<option value="${i.key}">${i.name}</option>`).join('')}</select>
                        </div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">员工人数</label><input type="number" id="c-employees" class="w-full" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">年营收（万元）</label><input type="number" id="c-revenue" class="w-full" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">数字化等级</label>
                            <select id="c-level" class="w-full">
                                <option value="unknown">未知</option>
                                <option value="level_2">二级</option>
                                <option value="level_3">三级</option>
                                <option value="level_4">四级</option>
                            </select>
                        </div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">地址</label><input id="c-address" class="w-full" /></div>
                        <div><label class="block text-sm font-medium text-gray-700 mb-1">备注</label><textarea id="c-remark" class="w-full" rows="2"></textarea></div>
                        <div class="flex gap-2 pt-2">
                            <button onclick="saveClient()" class="btn-primary">保存</button>
                            <a href="#clients" class="btn-secondary">取消</a>
                        </div>
                    </div>
                </div>
            `;
            renderInternalLayout(formContent);
            window.saveClient = async () => {
                const data = {
                    company_name: document.getElementById('c-name').value,
                    contact_name: document.getElementById('c-contact').value,
                    contact_phone: document.getElementById('c-phone').value,
                    industry: document.getElementById('c-industry').value,
                    employee_count: parseInt(document.getElementById('c-employees').value) || null,
                    annual_revenue: parseFloat(document.getElementById('c-revenue').value) || 0,
                    digital_level: document.getElementById('c-level').value,
                    address: document.getElementById('c-address').value,
                    remark: document.getElementById('c-remark').value,
                };
                if (!data.company_name) { alert('请填写企业名称'); return; }
                try {
                    await apiClient.createClient(data);
                    window.location.hash = 'clients';
                } catch (e) { alert(e.message); }
            };
        };
    };

    renderList();
}

async function renderClientDetail(clientId) {
    const client = await apiClient.getClient(clientId).catch(() => null);
    if (!client) { alert('客户不存在'); window.location.hash = 'clients'; return; }

    const projects = await apiClient.listProjects().catch(() => []);
    const clientProjects = projects.filter(p => p.client_id === clientId);

    renderInternalLayout(`
        <div class="mb-4">
            <a href="#clients" class="text-gray-500 hover:text-gray-700 text-sm">← 返回客户列表</a>
        </div>
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <div class="flex justify-between items-start">
                <div>
                    <h2 class="text-xl font-bold">${client.company_name}</h2>
                    <div class="text-sm text-gray-500 mt-1">${_industryName(client.industry)} · ${LEVEL_LABELS[client.digital_level] || '等级未知'}</div>
                </div>
                <button onclick="editClient()" class="btn-secondary text-sm">编辑</button>
            </div>
            <div class="grid md:grid-cols-3 gap-4 mt-4 text-sm">
                <div><span class="text-gray-400">联系人：</span>${client.contact_name || '-'} ${client.contact_phone || ''}</div>
                <div><span class="text-gray-400">员工数：</span>${client.employee_count || '-'}</div>
                <div><span class="text-gray-400">年营收：</span>${client.annual_revenue ? client.annual_revenue + ' 万元' : '-'}</div>
                <div class="md:col-span-3"><span class="text-gray-400">地址：</span>${client.address || '-'}</div>
                <div class="md:col-span-3"><span class="text-gray-400">备注：</span>${client.remark || '-'}</div>
            </div>
        </div>
        <div class="flex justify-between items-center mb-4">
            <h3 class="font-bold">关联项目</h3>
            <a href="#project-new" onclick="preselectClient(${client.id}); return false;" class="btn-primary text-sm">+ 为该客户新建项目</a>
        </div>
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <table class="min-w-full text-sm">
                <thead class="bg-gray-50 text-gray-600">
                    <tr><th class="px-4 py-3 text-left">项目编号</th><th class="px-4 py-3 text-left">项目名称</th><th class="px-4 py-3 text-left">状态</th><th class="px-4 py-3 text-left">预估补贴</th><th class="px-4 py-3 text-right">操作</th></tr>
                </thead>
                <tbody class="divide-y divide-gray-100">
                    ${clientProjects.length ? clientProjects.map(p => `
                        <tr class="hover:bg-gray-50">
                            <td class="px-4 py-3">${p.project_no || '-'}</td>
                            <td class="px-4 py-3 font-medium">${p.project_name}</td>
                            <td class="px-4 py-3"><span class="status-badge status-${p.status}">${STATUS_LABELS[p.status] || p.status}</span></td>
                            <td class="px-4 py-3">¥ ${p.estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</td>
                            <td class="px-4 py-3 text-right"><a href="#project/${p.id}" class="text-blue-600 hover:underline">详情</a></td>
                        </tr>
                    `).join('') : '<tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">暂无项目</td></tr>'}
                </tbody>
            </table>
        </div>
    `);

    window.editClient = () => {
        renderInternalLayout(`
            <div class="max-w-xl mx-auto">
                <h2 class="text-xl font-bold mb-4">编辑客户</h2>
                <div class="bg-white rounded-lg shadow p-6 space-y-4">
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">企业名称 *</label><input id="c-name" class="w-full" value="${client.company_name}" /></div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">联系人</label><input id="c-contact" class="w-full" value="${client.contact_name || ''}" /></div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">联系电话</label><input id="c-phone" class="w-full" value="${client.contact_phone || ''}" /></div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">所属行业</label>
                        <select id="c-industry" class="w-full"><option value="">请选择</option>${industries.map(i => `<option value="${i.key}" ${client.industry === i.key ? 'selected' : ''}>${i.name}</option>`).join('')}</select>
                    </div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">员工人数</label><input type="number" id="c-employees" class="w-full" value="${client.employee_count || ''}" /></div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">年营收（万元）</label><input type="number" id="c-revenue" class="w-full" value="${client.annual_revenue || ''}" /></div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">数字化等级</label>
                        <select id="c-level" class="w-full">
                            <option value="unknown" ${client.digital_level === 'unknown' ? 'selected' : ''}>未知</option>
                            <option value="level_2" ${client.digital_level === 'level_2' ? 'selected' : ''}>二级</option>
                            <option value="level_3" ${client.digital_level === 'level_3' ? 'selected' : ''}>三级</option>
                            <option value="level_4" ${client.digital_level === 'level_4' ? 'selected' : ''}>四级</option>
                        </select>
                    </div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">地址</label><input id="c-address" class="w-full" value="${client.address || ''}" /></div>
                    <div><label class="block text-sm font-medium text-gray-700 mb-1">备注</label><textarea id="c-remark" class="w-full" rows="2">${client.remark || ''}</textarea></div>
                    <div class="flex gap-2 pt-2">
                        <button onclick="saveEditClient()" class="btn-primary">保存</button>
                        <a href="#client/${clientId}" class="btn-secondary">取消</a>
                        <button onclick="deleteClient()" class="btn-danger ml-auto">删除</button>
                    </div>
                </div>
            </div>
        `);
        window.saveEditClient = async () => {
            const data = {
                company_name: document.getElementById('c-name').value,
                contact_name: document.getElementById('c-contact').value,
                contact_phone: document.getElementById('c-phone').value,
                industry: document.getElementById('c-industry').value,
                employee_count: parseInt(document.getElementById('c-employees').value) || null,
                annual_revenue: parseFloat(document.getElementById('c-revenue').value) || 0,
                digital_level: document.getElementById('c-level').value,
                address: document.getElementById('c-address').value,
                remark: document.getElementById('c-remark').value,
            };
            try { await apiClient.updateClient(clientId, data); window.location.hash = `client/${clientId}`; }
            catch (e) { alert(e.message); }
        };
        window.deleteClient = async () => {
            if (!confirm('确定删除该客户？')) return;
            try { await apiClient.deleteClient(clientId); window.location.hash = 'clients'; }
            catch (e) { alert(e.message); }
        };
    };
}

async function renderProjects() {
    let statusFilter = '';
    let projects = await apiClient.listProjects().catch(() => []);

    const refresh = async () => {
        const params = statusFilter ? `status=${encodeURIComponent(statusFilter)}` : '';
        projects = await apiClient.listProjects(params).catch(() => []);
        renderList();
    };

    const renderList = () => {
        renderInternalLayout(`
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">项目管理</h2>
                <a href="#project-new" class="btn-primary text-sm">+ 新建项目</a>
            </div>
            <div class="mb-4 flex gap-2">
                <select id="status-filter" class="w-40" onchange="window.filterStatus(this.value)">
                    <option value="">全部状态</option>
                    ${Object.entries(STATUS_LABELS).map(([k, v]) => `<option value="${k}" ${statusFilter === k ? 'selected' : ''}>${v}</option>`).join('')}
                </select>
            </div>
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <table class="min-w-full text-sm">
                    <thead class="bg-gray-50 text-gray-600">
                        <tr>
                            <th class="px-4 py-3 text-left">项目编号</th>
                            <th class="px-4 py-3 text-left">项目名称</th>
                            <th class="px-4 py-3 text-left">客户</th>
                            <th class="px-4 py-3 text-left">状态</th>
                            <th class="px-4 py-3 text-left">签订日期</th>
                            <th class="px-4 py-3 text-right">预估补贴</th>
                            <th class="px-4 py-3 text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        ${projects.length ? projects.map(p => `
                            <tr class="hover:bg-gray-50">
                                <td class="px-4 py-3">${p.project_no || '-'}</td>
                                <td class="px-4 py-3 font-medium">${p.project_name}</td>
                                <td class="px-4 py-3">${p.client_name || '-'}</td>
                                <td class="px-4 py-3"><span class="status-badge status-${p.status}">${STATUS_LABELS[p.status] || p.status}</span></td>
                                <td class="px-4 py-3">${p.contract_sign_date || '-'}</td>
                                <td class="px-4 py-3 text-right">¥ ${p.estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</td>
                                <td class="px-4 py-3 text-right">
                                    <a href="#project/${p.id}" class="text-blue-600 hover:underline">详情</a>
                                </td>
                            </tr>
                        `).join('') : '<tr><td colspan="7" class="px-4 py-8 text-center text-gray-400">暂无项目</td></tr>'}
                    </tbody>
                </table>
            </div>
        `);
        window.filterStatus = (val) => { statusFilter = val; refresh(); };
    };

    renderList();
}

let _preselectedClientId = null;
function preselectClient(id) { _preselectedClientId = id; window.location.hash = 'project-new'; }

async function renderProjectNew() {
    if (!industries.length) industries = await apiClient.industries().catch(() => []);
    const clients = await apiClient.listClients().catch(() => []);

    renderInternalLayout(`
        <div class="max-w-2xl mx-auto">
            <h2 class="text-xl font-bold mb-4">新建申报项目</h2>
            <div class="bg-white rounded-lg shadow p-6 space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">选择客户 *</label>
                    <select id="p-client" class="w-full">
                        <option value="">请选择</option>
                        ${clients.map(c => `<option value="${c.id}" ${_preselectedClientId == c.id ? 'selected' : ''}>${c.company_name}</option>`).join('')}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">项目名称 *</label>
                    <input id="p-name" class="w-full" placeholder="例如：XX公司数字化改造一期" />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">目标数字化等级 *</label>
                    <select id="p-level" class="w-full">
                        <option value="">请选择</option>
                        <option value="level_2">二级（上限 60 万）</option>
                        <option value="level_3">三级（上限 200 万）</option>
                        <option value="level_4">四级（上限 500 万）</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">合同类型</label>
                    <select id="p-contract-type" class="w-full">
                        <option value="">请选择</option>
                        <option value="two_party">两方合同</option>
                        <option value="multi_party">多方合同</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">合同签订日期</label>
                    <input type="date" id="p-contract-date" class="w-full" />
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">合同总金额（元）</label>
                    <input type="number" id="p-contract-amount" class="w-full" />
                </div>
                <div class="flex gap-2 pt-2">
                    <button onclick="saveProject()" class="btn-primary">保存草稿</button>
                    <a href="#projects" class="btn-secondary">取消</a>
                </div>
            </div>
        </div>
    `);
    _preselectedClientId = null;

    window.saveProject = async () => {
        const data = {
            client_id: parseInt(document.getElementById('p-client').value),
            project_name: document.getElementById('p-name').value,
            digital_level: document.getElementById('p-level').value,
            contract_type: document.getElementById('p-contract-type').value,
            contract_sign_date: document.getElementById('p-contract-date').value,
            contract_amount: parseFloat(document.getElementById('p-contract-amount').value) || 0,
        };
        if (!data.client_id || !data.project_name || !data.digital_level) {
            alert('请填写必填项'); return;
        }
        try {
            const res = await apiClient.createProject(data);
            window.location.hash = `project/${res.id}`;
        } catch (e) { alert(e.message); }
    };
}

async function renderProjectDetail(projectId) {
    const project = await apiClient.getProject(projectId).catch(() => null);
    if (!project) { alert('项目不存在'); window.location.hash = 'projects'; return; }

    const nextStatuses = {
        draft: ['contract_signed', 'rejected'],
        contract_signed: ['implementing', 'rejected'],
        implementing: ['audit_pending', 'rejected'],
        audit_pending: ['audit_done', 'rejected'],
        audit_done: ['acceptance_pending', 'rejected'],
        acceptance_pending: ['accepted', 'rejected'],
        accepted: ['subsidy_approved', 'rejected'],
        subsidy_approved: ['subsidy_paid'],
        rejected: ['draft'],
    }[project.status] || [];

    renderInternalLayout(`
        <div class="mb-4">
            <a href="#projects" class="text-gray-500 hover:text-gray-700 text-sm">← 返回项目列表</a>
        </div>
        <div class="grid lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 space-y-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <div class="text-xs text-gray-400 mb-1">${project.project_no || '-'}</div>
                            <h2 class="text-xl font-bold">${project.project_name}</h2>
                        </div>
                        <span class="status-badge status-${project.status}">${STATUS_LABELS[project.status] || project.status}</span>
                    </div>
                    <div class="grid md:grid-cols-2 gap-4 text-sm">
                        <div><span class="text-gray-400">客户：</span>${project.client_name || '-'}</div>
                        <div><span class="text-gray-400">负责人：</span>${project.agent_name || '-'}</div>
                        <div><span class="text-gray-400">数字化等级：</span>${LEVEL_LABELS[project.digital_level] || project.digital_level}</div>
                        <div><span class="text-gray-400">合同类型：</span>${project.contract_type === 'two_party' ? '两方合同' : project.contract_type === 'multi_party' ? '多方合同' : '-'}</div>
                        <div><span class="text-gray-400">签订日期：</span>${project.contract_sign_date || '-'}</div>
                        <div><span class="text-gray-400">合同金额：</span>${project.contract_amount ? '¥ ' + project.contract_amount.toLocaleString() : '-'}</div>
                    </div>
                    ${project.compliance_result && project.compliance_result.compliant !== undefined ? `
                        <div class="mt-4 p-3 rounded text-sm ${project.compliance_result.compliant ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}">
                            <div class="font-bold mb-1">合规校验结果：${project.compliance_result.compliant ? '✅ 合规' : '❌ 不合规'}</div>
                            ${project.compliance_result.reasons.map(r => `<div>• ${r}</div>`).join('')}
                        </div>
                    ` : ''}
                    ${project.rejection_reason ? `<div class="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm"><span class="font-bold">驳回原因：</span>${project.rejection_reason}</div>` : ''}
                    <div class="mt-4 flex gap-2 flex-wrap">
                        ${project.status === 'draft' || project.status === 'rejected' ? `<a href="#project-edit/${project.id}" class="btn-secondary text-sm">编辑信息</a>` : ''}
                        <a href="#project-expenses/${project.id}" class="btn-secondary text-sm">管理投资明细</a>
                        ${nextStatuses.map(s => `<button onclick="transitionProject('${s}')" class="${s === 'rejected' ? 'btn-danger' : 'btn-success'} text-sm">${STATUS_LABELS[s] || s}</button>`).join('')}
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="font-bold mb-4">投资明细</h3>
                    ${project.expenses.length ? `
                        <table class="min-w-full text-sm mb-3">
                            <thead class="bg-gray-50 text-gray-600">
                                <tr><th class="px-3 py-2 text-left">类别</th><th class="px-3 py-2 text-left">说明</th><th class="px-3 py-2 text-right">金额</th><th class="px-3 py-2 text-center">可补贴</th></tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100">
                                ${project.expenses.map(e => `
                                    <tr>
                                        <td class="px-3 py-2">${EXPENSE_CATEGORIES.find(c => c.value === e.category)?.label || e.category}</td>
                                        <td class="px-3 py-2 text-gray-500">${e.description || '-'}</td>
                                        <td class="px-3 py-2 text-right">${e.amount.toLocaleString()}</td>
                                        <td class="px-3 py-2 text-center">${e.is_subsidiable ? '<span class="text-green-600 font-bold">是</span>' : '<span class="text-red-400">否</span>'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        <div class="grid grid-cols-3 gap-2 text-sm bg-gray-50 rounded p-3">
                            <div><div class="text-gray-400">可补贴合计</div><div class="font-bold text-green-700">¥ ${project.eligible_total.toLocaleString()}</div></div>
                            <div><div class="text-gray-400">不可补贴合计</div><div class="font-bold text-red-400">¥ ${project.ineligible_total.toLocaleString()}</div></div>
                            <div><div class="text-gray-400">预估补贴</div><div class="font-bold text-blue-700">¥ ${project.estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</div></div>
                        </div>
                    ` : '<div class="text-gray-400 text-sm">暂无投资明细，<a href="#project-expenses/' + project.id + '" class="text-blue-600">去添加</a></div>'}
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="font-bold mb-4">操作日志</h3>
                    <div class="space-y-3 text-sm">
                        ${project.logs.length ? project.logs.map(l => `
                            <div class="flex gap-3">
                                <div class="text-gray-400 whitespace-nowrap">${new Date(l.created_at).toLocaleString('zh-CN')}</div>
                                <div><span class="font-medium">${l.user_name || '-'}</span> · ${l.action} · ${l.comment}</div>
                            </div>
                        `).join('') : '<div class="text-gray-400">暂无日志</div>'}
                    </div>
                </div>
            </div>

            <div class="space-y-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="font-bold mb-4">补贴概览</h3>
                    <div class="text-center mb-4">
                        <div class="text-sm text-gray-500">预估补贴</div>
                        <div class="text-3xl font-bold text-blue-700">¥ ${project.estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</div>
                    </div>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between"><span class="text-gray-500">已批准</span><span class="font-bold">¥ ${project.approved_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</span></div>
                        <div class="flex justify-between"><span class="text-gray-500">补贴比例</span><span class="font-bold">${(project.subsidy_rate_applied * 100).toFixed(1)}%</span></div>
                        <div class="flex justify-between"><span class="text-gray-500">等级上限</span><span class="font-bold">¥ ${({level_2: 600000, level_3: 2000000, level_4: 5000000}[project.digital_level] || 0).toLocaleString()}</span></div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="font-bold mb-4">附件</h3>
                    <div class="space-y-2 mb-3">
                        ${(project.attachments || []).length ? project.attachments.map(f => `
                            <div class="flex justify-between items-center text-sm bg-gray-50 rounded p-2">
                                <a href="/uploads/${f}" target="_blank" class="text-blue-600 hover:underline truncate max-w-[150px]">${f.slice(0, 20)}...</a>
                                <button onclick="deleteAttachment('${f}')" class="text-red-400 hover:text-red-600 text-xs">删除</button>
                            </div>
                        `).join('') : '<div class="text-gray-400 text-sm">暂无附件</div>'}
                    </div>
                    <input type="file" id="attach-file" class="text-sm" onchange="uploadAttachment(this)" />
                </div>
            </div>
        </div>
    `);

    window.transitionProject = async (toStatus) => {
        const comment = toStatus === 'rejected' ? prompt('请输入驳回原因/备注：') || '' : '';
        try {
            await apiClient.transitionProject(projectId, { to_status: toStatus, comment });
            window.location.reload();
        } catch (e) { alert(e.message); }
    };
    window.uploadAttachment = async (input) => {
        if (!input.files.length) return;
        try {
            await apiClient.uploadAttachment(projectId, input.files[0]);
            window.location.reload();
        } catch (e) { alert(e.message); }
    };
    window.deleteAttachment = async (filename) => {
        if (!confirm('确定删除该附件？')) return;
        try {
            await apiClient.deleteAttachment(projectId, filename);
            window.location.reload();
        } catch (e) { alert(e.message); }
    };
}

async function renderProjectEdit(projectId) {
    const project = await apiClient.getProject(projectId).catch(() => null);
    if (!project) { alert('项目不存在'); return; }
    renderInternalLayout(`
        <div class="max-w-2xl mx-auto">
            <h2 class="text-xl font-bold mb-4">编辑项目</h2>
            <div class="bg-white rounded-lg shadow p-6 space-y-4">
                <div><label class="block text-sm font-medium text-gray-700 mb-1">项目名称 *</label><input id="p-name" class="w-full" value="${project.project_name}" /></div>
                <div><label class="block text-sm font-medium text-gray-700 mb-1">目标数字化等级 *</label>
                    <select id="p-level" class="w-full">
                        <option value="level_2" ${project.digital_level === 'level_2' ? 'selected' : ''}>二级（上限 60 万）</option>
                        <option value="level_3" ${project.digital_level === 'level_3' ? 'selected' : ''}>三级（上限 200 万）</option>
                        <option value="level_4" ${project.digital_level === 'level_4' ? 'selected' : ''}>四级（上限 500 万）</option>
                    </select>
                </div>
                <div><label class="block text-sm font-medium text-gray-700 mb-1">合同类型</label>
                    <select id="p-contract-type" class="w-full">
                        <option value="">请选择</option>
                        <option value="two_party" ${project.contract_type === 'two_party' ? 'selected' : ''}>两方合同</option>
                        <option value="multi_party" ${project.contract_type === 'multi_party' ? 'selected' : ''}>多方合同</option>
                    </select>
                </div>
                <div><label class="block text-sm font-medium text-gray-700 mb-1">合同签订日期</label><input type="date" id="p-contract-date" class="w-full" value="${project.contract_sign_date || ''}" /></div>
                <div><label class="block text-sm font-medium text-gray-700 mb-1">合同总金额（元）</label><input type="number" id="p-contract-amount" class="w-full" value="${project.contract_amount || ''}" /></div>
                <div class="flex gap-2 pt-2">
                    <button onclick="updateProject()" class="btn-primary">保存</button>
                    <a href="#project/${projectId}" class="btn-secondary">取消</a>
                </div>
            </div>
        </div>
    `);
    window.updateProject = async () => {
        const data = {
            project_name: document.getElementById('p-name').value,
            digital_level: document.getElementById('p-level').value,
            contract_type: document.getElementById('p-contract-type').value,
            contract_sign_date: document.getElementById('p-contract-date').value,
            contract_amount: parseFloat(document.getElementById('p-contract-amount').value) || 0,
        };
        try { await apiClient.updateProject(projectId, data); window.location.hash = `project/${projectId}`; }
        catch (e) { alert(e.message); }
    };
}

async function renderProjectExpenses(projectId) {
    const project = await apiClient.getProject(projectId).catch(() => null);
    if (!project) { alert('项目不存在'); return; }
    const expenses = await apiClient.listExpenses(projectId).catch(() => []);

    const renderPage = () => {
        const editable = project.status === 'draft' || project.status === 'rejected';
        renderInternalLayout(`
            <div class="mb-4">
                <a href="#project/${projectId}" class="text-gray-500 hover:text-gray-700 text-sm">← 返回项目详情</a>
            </div>
            <h2 class="text-xl font-bold mb-4">${project.project_name} - 投资明细管理</h2>

            <div class="grid lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-lg shadow overflow-hidden">
                        <table class="min-w-full text-sm">
                            <thead class="bg-gray-50 text-gray-600">
                                <tr>
                                    <th class="px-4 py-3 text-left">类别</th>
                                    <th class="px-4 py-3 text-left">说明</th>
                                    <th class="px-4 py-3 text-right">金额</th>
                                    <th class="px-4 py-3 text-center">可补贴</th>
                                    ${editable ? '<th class="px-4 py-3 text-right">操作</th>' : ''}
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100">
                                ${expenses.length ? expenses.map(e => `
                                    <tr class="hover:bg-gray-50">
                                        <td class="px-4 py-3">${EXPENSE_CATEGORIES.find(c => c.value === e.category)?.label || e.category}</td>
                                        <td class="px-4 py-3 text-gray-500">${e.description || '-'}</td>
                                        <td class="px-4 py-3 text-right">${e.amount.toLocaleString()}</td>
                                        <td class="px-4 py-3 text-center">${e.is_subsidiable ? '<span class="text-green-600 font-bold">是</span>' : '<span class="text-red-400">否</span>'}</td>
                                        ${editable ? `<td class="px-4 py-3 text-right"><button onclick="deleteExpenseItem(${e.id})" class="text-red-400 hover:text-red-600 text-xs">删除</button></td>` : ''}
                                    </tr>
                                `).join('') : '<tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">暂无投资明细</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="space-y-6">
                    ${editable ? `
                        <div class="bg-white rounded-lg shadow p-6">
                            <h3 class="font-bold mb-4">添加投资明细</h3>
                            <div class="space-y-3">
                                <div>
                                    <label class="block text-xs text-gray-500 mb-1">费用类别</label>
                                    <select id="e-category" class="w-full text-sm">
                                        ${EXPENSE_CATEGORIES.map(c => `<option value="${c.value}">${c.label} ${c.subsidiable ? '(可补贴)' : '(不可补贴)'}</option>`).join('')}
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-xs text-gray-500 mb-1">说明</label>
                                    <input id="e-desc" class="w-full text-sm" placeholder="例如：MES系统采购" />
                                </div>
                                <div>
                                    <label class="block text-xs text-gray-500 mb-1">金额（元）</label>
                                    <input type="number" id="e-amount" class="w-full text-sm" placeholder="0" />
                                </div>
                                <div>
                                    <label class="block text-xs text-gray-500 mb-1">发票号码</label>
                                    <input id="e-invoice" class="w-full text-sm" />
                                </div>
                                <div>
                                    <label class="block text-xs text-gray-500 mb-1">供应商</label>
                                    <input id="e-vendor" class="w-full text-sm" />
                                </div>
                                <button onclick="addExpense()" class="btn-primary w-full text-sm">添加</button>
                            </div>
                        </div>
                    ` : '<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-700">当前项目状态不可编辑投资明细</div>'}

                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="font-bold mb-4">实时汇总</h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between"><span class="text-gray-500">可补贴合计</span><span class="font-bold text-green-700">¥ ${project.eligible_total.toLocaleString()}</span></div>
                            <div class="flex justify-between"><span class="text-gray-500">不可补贴合计</span><span class="font-bold text-red-400">¥ ${project.ineligible_total.toLocaleString()}</span></div>
                            <div class="border-t pt-2 flex justify-between"><span class="text-gray-700 font-medium">预估补贴</span><span class="font-bold text-blue-700 text-lg">¥ ${project.estimated_subsidy.toLocaleString('zh-CN', {maximumFractionDigits: 0})}</span></div>
                        </div>
                    </div>
                </div>
            </div>
        `);
    };

    renderPage();

    window.addExpense = async () => {
        const data = {
            category: document.getElementById('e-category').value,
            description: document.getElementById('e-desc').value,
            amount: parseFloat(document.getElementById('e-amount').value) || 0,
            invoice_no: document.getElementById('e-invoice').value,
            vendor_name: document.getElementById('e-vendor').value,
        };
        if (!data.amount) { alert('请填写金额'); return; }
        try {
            await apiClient.createExpense(projectId, data);
            const refreshed = await apiClient.getProject(projectId);
            project.eligible_total = refreshed.eligible_total;
            project.ineligible_total = refreshed.ineligible_total;
            project.estimated_subsidy = refreshed.estimated_subsidy;
            const newExpenses = await apiClient.listExpenses(projectId);
            expenses.length = 0;
            expenses.push(...newExpenses);
            renderPage();
            document.getElementById('e-desc').value = '';
            document.getElementById('e-amount').value = '';
            document.getElementById('e-invoice').value = '';
            document.getElementById('e-vendor').value = '';
        } catch (e) { alert(e.message); }
    };

    window.deleteExpenseItem = async (expenseId) => {
        if (!confirm('确定删除该投资明细？')) return;
        try {
            await apiClient.deleteExpense(expenseId);
            const refreshed = await apiClient.getProject(projectId);
            project.eligible_total = refreshed.eligible_total;
            project.ineligible_total = refreshed.ineligible_total;
            project.estimated_subsidy = refreshed.estimated_subsidy;
            const newExpenses = await apiClient.listExpenses(projectId);
            expenses.length = 0;
            expenses.push(...newExpenses);
            renderPage();
        } catch (e) { alert(e.message); }
    };
}

// ===================== 辅助函数 =====================
function _industryName(key) {
    const found = industries.find(i => i.key === key);
    return found ? found.name : (key || '-');
}

// ===================== 初始化 =====================
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
    industries = await apiClient.industries().catch(() => []);
    route();
    window.addEventListener('hashchange', route);
}

init();
