const app = document.getElementById("app");
let currentUser = null;
let signatureBox = null;

const STATUS_MAP = {
    draft: "草稿",
    pending_manager: "待项目负责人签字",
    pending_dept: "待部门负责人签字",
    pending_marketing: "待营销管理中心确认",
    pending_tech: "待技术质量管理确认",
    approved: "已完成",
    rejected: "已驳回"
};

const ROLE_MAP = {
    project_taker: "项目承接人",
    project_manager: "项目负责人",
    dept_head: "部门负责人",
    marketing: "营销管理中心",
    tech_quality: "技术质量管理",
    admin: "管理员"
};

function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function init() {
    const hash = window.location.hash || "#login";
    token = localStorage.getItem("token") || "";
    if (token && hash !== "#login") {
        try {
            currentUser = await api.me();
        } catch (e) {
            token = "";
            localStorage.removeItem("token");
        }
    }
    route();
    window.addEventListener("hashchange", route);
}

function route() {
    const hash = window.location.hash || "#login";
    if (!token && hash !== "#login") {
        window.location.hash = "#login";
        return;
    }
    if (hash === "#login") {
        renderLogin();
    } else if (hash === "#list") {
        renderList();
    } else if (hash.startsWith("#form/")) {
        const id = hash.split("/")[1];
        renderFormEditor(id);
    } else if (hash.startsWith("#view/")) {
        const id = hash.split("/")[1];
        renderFormViewer(id);
    } else if (hash.startsWith("#approve/")) {
        const id = hash.split("/")[1];
        renderApproval(id);
    } else if (hash.startsWith("#pdf/")) {
        const id = hash.split("/")[1];
        renderPdfPreview(id);
    } else {
        window.location.hash = "#list";
    }
}

function renderLogin() {
    app.innerHTML = `
        <div class="min-h-screen flex items-center justify-center">
            <div class="bg-white p-8 rounded shadow-md w-full max-w-md">
                <h1 class="text-2xl font-bold mb-6 text-center">合同流转确认单系统</h1>
                <form id="loginForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium">用户名</label>
                        <input type="text" id="username" class="w-full border rounded px-3 py-2" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium">密码</label>
                        <input type="password" id="password" class="w-full border rounded px-3 py-2" required>
                    </div>
                    <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">登录</button>
                </form>
                <div class="mt-4 text-xs text-gray-500">
                    <p>默认账号：</p>
                    <p>admin / admin123 (管理员)</p>
                    <p>chengjie / 123456 (项目承接人)</p>
                    <p>fuze / 123456 (项目负责人)</p>
                    <p>bumen / 123456 (部门负责人)</p>
                    <p>yingxiao / 123456 (营销管理)</p>
                    <p>jishu / 123456 (技术质量)</p>
                </div>
            </div>
        </div>
    `;
    document.getElementById("loginForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const u = document.getElementById("username").value;
        const p = document.getElementById("password").value;
        try {
            const res = await api.login(u, p);
            token = res.access_token;
            localStorage.setItem("token", token);
            currentUser = res.user;
            window.location.hash = "#list";
        } catch (err) {
            alert(err.message);
        }
    });
}

async function renderList() {
    app.innerHTML = `<div class="p-4 max-w-7xl mx-auto">
        <div class="bg-white p-4 rounded shadow mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
                <span class="font-bold">当前用户：</span>
                <span>${currentUser.real_name}</span>
                <span class="text-gray-500 text-sm">(${ROLE_MAP[currentUser.role]})</span>
            </div>
            <div class="flex gap-2">
                ${currentUser.role === "project_taker" || currentUser.role === "admin" ? `<button onclick="location.hash='#form/new'" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">新建表单</button>` : ""}
                <button id="btnExport" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">导出Excel</button>
                ${currentUser.role === "admin" ? `<button id="btnImport" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">导入Excel</button><input type="file" id="importFile" class="hidden" accept=".xlsx,.xls">` : ""}
                <button onclick="logout()" class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">退出</button>
            </div>
        </div>
        <div class="bg-white rounded shadow overflow-hidden">
            <div class="p-3 border-b flex gap-2 overflow-x-auto">
                <button class="status-filter px-3 py-1 text-sm rounded bg-blue-100 text-blue-700" data-status="">全部</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="draft">草稿</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="pending_manager">待负责人</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="pending_dept">待部门</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="pending_marketing">待营销</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="pending_tech">待技术</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="approved">已完成</button>
                <button class="status-filter px-3 py-1 text-sm rounded hover:bg-gray-100" data-status="rejected">已驳回</button>
            </div>
            <table class="w-full text-sm">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-4 py-2 text-left">商机号</th>
                        <th class="px-4 py-2 text-left">工程名称</th>
                        <th class="px-4 py-2 text-left">委托单位</th>
                        <th class="px-4 py-2 text-left">结账号</th>
                        <th class="px-4 py-2 text-left">状态</th>
                        <th class="px-4 py-2 text-left">附件</th>
                        <th class="px-4 py-2 text-left">创建人</th>
                        <th class="px-4 py-2 text-left">创建时间</th>
                        <th class="px-4 py-2 text-left">操作</th>
                    </tr>
                </thead>
                <tbody id="formListBody" class="divide-y"></tbody>
            </table>
        </div>
    </div>`;

    loadForms("");

    document.querySelectorAll(".status-filter").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".status-filter").forEach(b => { b.classList.remove("bg-blue-100", "text-blue-700"); b.classList.add("hover:bg-gray-100"); });
            btn.classList.remove("hover:bg-gray-100");
            btn.classList.add("bg-blue-100", "text-blue-700");
            const s = btn.dataset.status;
            loadForms(s ? `?status=${s}` : "");
        });
    });

    document.getElementById("btnExport")?.addEventListener("click", async () => {
        try {
            const blob = await api.exportForms();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "合同流转单导出.xlsx";
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) { alert(e.message); }
    });

    const btnImport = document.getElementById("btnImport");
    const importFile = document.getElementById("importFile");
    if (btnImport) {
        btnImport.addEventListener("click", () => importFile.click());
        importFile.addEventListener("change", async () => {
            if (!importFile.files[0]) return;
            try {
                const res = await api.importForms(importFile.files[0]);
                alert(`导入完成：成功 ${res.success} 条，失败 ${res.failed} 条`);
                loadForms("");
            } catch (e) { alert(e.message); }
        });
    }
}

async function loadForms(query) {
    const tbody = document.getElementById("formListBody");
    tbody.innerHTML = `<tr><td colspan="8" class="px-4 py-4 text-center text-gray-400">加载中...</td></tr>`;
    try {
        const forms = await api.listForms(query);
        if (!forms.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="px-4 py-4 text-center text-gray-400">暂无数据</td></tr>`;
            return;
        }
        tbody.innerHTML = forms.map(f => {
            let actions = `<button onclick="location.hash='#view/${f.id}'" class="text-blue-600 hover:underline mr-2">查看</button>`;
            const canEdit = (f.status === "draft" || f.status === "rejected") && (currentUser.role === "project_taker" || currentUser.role === "admin");
            const adminCanEdit = currentUser.role === "admin";
            if (canEdit || adminCanEdit) {
                actions += `<button onclick="location.hash='#form/${f.id}'" class="text-blue-600 hover:underline mr-2">编辑</button>`;
            }
            if (canApprove(f.status)) {
                actions += `<button onclick="location.hash='#approve/${f.id}'" class="text-green-600 hover:underline mr-2">审批</button>`;
            }
            actions += `<button onclick="location.hash='#pdf/${f.id}'" class="text-purple-600 hover:underline">打印PDF</button>`;
            return `<tr>
                <td class="px-4 py-2">${f.business_opportunity_no || "-"}</td>
                <td class="px-4 py-2">${f.project_name || "-"}</td>
                <td class="px-4 py-2">${f.client_unit || "-"}</td>
                <td class="px-4 py-2">${f.platform_account || "-"}</td>
                <td class="px-4 py-2"><span class="px-2 py-1 rounded text-xs ${statusBadgeClass(f.status)}">${STATUS_MAP[f.status]}</span></td>
                <td class="px-4 py-2">${renderAttachments(f.id, f.attachments)}</td>
                <td class="px-4 py-2">${f.creator_name || "-"}</td>
                <td class="px-4 py-2">${formatDate(f.created_at)}</td>
                <td class="px-4 py-2">${actions}</td>
            </tr>`;
        }).join("");
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="9" class="px-4 py-4 text-center text-red-500">加载失败：${e.message}</td></tr>`;
    }
}

function renderAttachmentsReadOnly(attachments) {
    const atts = attachments || [];
    if (!atts.length) return "";
    const listHtml = atts.map(a => {
        const displayName = a.split("|")[0];
        const uniqueName = a.split("|")[1];
        return `<a href="/uploads/${encodeURIComponent(uniqueName)}" target="_blank" class="text-blue-600 hover:underline text-sm mr-3">${escapeHtml(displayName)}</a>`;
    }).join("");
    return `
    <div class="bg-white p-4 rounded shadow mt-4 no-print">
        <h3 class="font-bold mb-2 text-sm">附件</h3>
        <div class="flex flex-wrap gap-1">${listHtml}</div>
    </div>`;
}

function renderAttachments(formId, attachments) {
    if (!attachments || !attachments.length) return "-";
    return attachments.map(a => {
        const displayName = a.split("|")[0];
        return `<a href="/uploads/${encodeURIComponent(a.split("|")[1])}" target="_blank" class="text-blue-600 hover:underline text-xs block" title="${escapeHtml(displayName)}">${escapeHtml(displayName)}</a>`;
    }).join("");
}

function canApprove(status) {
    const map = {
        pending_manager: ["project_manager", "admin"],
        pending_dept: ["dept_head", "admin"],
        pending_marketing: ["marketing", "admin"],
        pending_tech: ["tech_quality", "admin"]
    };
    return (map[status] || []).includes(currentUser.role);
}

function statusBadgeClass(status) {
    const map = {
        draft: "bg-gray-100 text-gray-700",
        pending_manager: "bg-yellow-100 text-yellow-700",
        pending_dept: "bg-yellow-100 text-yellow-700",
        pending_marketing: "bg-orange-100 text-orange-700",
        pending_tech: "bg-orange-100 text-orange-700",
        approved: "bg-green-100 text-green-700",
        rejected: "bg-red-100 text-red-700"
    };
    return map[status] || "bg-gray-100";
}

function formatDate(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")} ${String(d.getHours()).padStart(2,"0")}:${String(d.getMinutes()).padStart(2,"0")}`;
}

function logout() {
    localStorage.removeItem("token");
    token = "";
    currentUser = null;
    window.location.hash = "#login";
}

function generateFormHTML(data, readonly) {
    const d = data || {};
    const disabled = readonly ? "disabled" : "";
    const sigMap = {};
    if (d.signatures) {
        d.signatures.forEach(s => { sigMap[s.role] = s; });
    }

    const sigImg = (role) => {
        const s = sigMap[role];
        if (!s) return '';
        return `<img src="${s.signature_data}" class="h-8 max-w-[120px] object-contain inline-block" />`;
    };

    const inputStyle = readonly ? 'border:none;background:transparent;width:100%;box-sizing:border-box;' : 'border:1px solid #999;border-radius:2px;padding:2px 4px;width:100%;box-sizing:border-box;';
    const txt = (name, val, placeholder="") => `<input type="text" name="${name}" value="${escapeHtml(val || '')}" placeholder="${placeholder}" ${disabled} style="${inputStyle}">`;
    const num = (name, val) => `<input type="number" name="${name}" value="${val !== undefined && val !== null ? val : ''}" step="0.01" ${disabled} style="${inputStyle}text-align:right;">`;
    const dt = (name, val) => `<input type="date" name="${name}" value="${val || ''}" ${disabled} style="${inputStyle}">`;
    const cb = (name, label, val) => {
        if (readonly) {
            return `<span class="inline-flex items-center mr-2 text-sm"><span class="mr-1">${val ? '☑' : '☐'}</span>${label}</span>`;
        }
        return `<label class="inline-flex items-center mr-2 text-sm cursor-pointer"><input type="checkbox" name="${name}" ${val ? 'checked' : ''} ${disabled} class="mr-1 align-middle">${label}</label>`;
    };

    const signCell = (roleText, roleKey) => `
        <div style="min-height:55px;" class="flex flex-col justify-end">
            <div class="text-sm mb-1">${roleText}（签名）</div>
            <div class="flex items-end">
                <div class="flex-1 border-b border-gray-800 h-8 text-center leading-8">${sigImg(roleKey)}</div>
                <div class="ml-2 text-sm whitespace-nowrap">日期：</div>
                <div class="w-20 border-b border-gray-800 h-8"></div>
            </div>
        </div>
    `;

    return `
    <div class="bg-white p-4 rounded shadow">
        <div class="flex justify-between items-start text-sm" style="margin-bottom:4px;">
            <div>上海中测行工程检测咨询有限公司</div>
            <div>JYY-ZCH-JF-P02-01-F03</div>
        </div>
        <h2 class="text-xl font-bold text-center" style="margin-bottom:4px;">合同流转确认单</h2>
        <div class="flex justify-between mb-2 text-sm">
            <span class="inline-flex items-center">项目负责人：${txt('project_manager_name', d.project_manager_name)}</span>
            <span class="inline-flex items-center">商机号：${txt('business_opportunity_no', d.business_opportunity_no)}</span>
        </div>
        <table class="form-table" style="table-layout:fixed;">
            <colgroup>
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
                <col style="width:11.11%">
            </colgroup>
            <tr>
                <td class="label-cell" style="width:70px;">委托单位</td>
                <td colspan="3">${txt('client_unit', d.client_unit)}</td>
                <td class="label-cell" style="width:70px;">工程名称</td>
                <td colspan="4">${txt('project_name', d.project_name)}</td>
            </tr>
            <tr>
                <td class="label-cell">付款单位</td>
                <td colspan="3">${txt('payer_unit', d.payer_unit)}</td>
                <td class="label-cell" style="width:70px;">结账号</td>
                <td colspan="4">${txt('platform_account', d.platform_account)}</td>
            </tr>
            <tr>
                <td class="label-cell">工程类别</td>
                <td colspan="8" class="text-sm">
                    ${cb('project_category_房建', '房建', d.project_category==='房建')}
                    ${cb('project_category_市政基础设施', '市政基础设施', d.project_category==='市政基础设施')}
                    ${cb('project_category_房屋修缮', '房屋修缮', d.project_category==='房屋修缮')}
                    ${cb('project_category_轨道交通', '轨道交通', d.project_category==='轨道交通')}
                    ${cb('project_category_水利', '水利', d.project_category==='水利')}
                    ${cb('project_category_民防', '民防', d.project_category==='民防')}
                    ${cb('project_category_公路', '公路', d.project_category==='公路')}
                    ${cb('project_category_绿化', '绿化', d.project_category==='绿化')}
                    ${cb('project_category_水运', '水运', d.project_category==='水运')}
                    ${cb('project_category_其他', '其他', d.project_category==='其他')}
                    <span class="ml-2">工程等级：${txt('project_level', d.project_level)}</span>
                    <span class="ml-2">批复文件</span>
                    ${cb('has_approval_document', '有', d.has_approval_document)}
                    ${cb('has_approval_document_no', '无', !d.has_approval_document)}
                </td>
            </tr>
            <tr>
                <td class="label-cell">检测类型</td>
                <td colspan="2" class="text-sm">
                    ${cb('inspection_type_施工检测', '施工检测', (d.inspection_type||'').includes('施工检测'))}
                    ${cb('inspection_type_监理平行检测', '监理平行检测', (d.inspection_type||'').includes('监理平行检测'))}
                    ${cb('inspection_type_监督抽检', '监督抽检', (d.inspection_type||'').includes('监督抽检'))}
                    ${cb('inspection_type_其他', '其他', (d.inspection_type||'').includes('其他'))}
                </td>
                <td class="label-cell" style="width:60px;">项目区域</td>
                <td>${txt('project_region', d.project_region)}</td>
                <td class="label-cell" style="width:60px;">合作单位</td>
                <td class="text-sm">
                    ${cb('has_cooperation_unit', '有', d.has_cooperation_unit)}
                    ${cb('has_cooperation_unit_no', '无', !d.has_cooperation_unit)}
                </td>
                <td class="label-cell" style="width:40px;">备注</td>
                <td>${txt('remark', d.remark)}</td>
            </tr>
            <tr>
                <td class="label-cell">工程建设周期</td>
                <td class="flex items-center" style="padding:4px 6px;">${txt('construction_cycle_months', d.construction_cycle_months)}<span class="ml-1">月</span></td>
                <td class="label-cell" style="width:80px;">预计开始时间</td>
                <td>${dt('estimated_start_date', d.estimated_start_date)}</td>
                <td class="label-cell" style="width:80px;">实际开工时间</td>
                <td colspan="4">${dt('actual_start_date', d.actual_start_date)}</td>
            </tr>
            <tr>
                <td class="label-cell">合同总价<br>（元）</td>
                <td>${num('contract_total_price', d.contract_total_price)}</td>
                <td class="label-cell">折扣率<br>（%）</td>
                <td>${num('discount_rate', d.discount_rate)}</td>
                <td class="label-cell">配合费<br>（元）</td>
                <td>${num('coordination_fee', d.coordination_fee)}</td>
                <td class="label-cell">劳务费<br>（元）</td>
                <td>${num('labor_fee', d.labor_fee)}</td>
                <td>${num('material_fee', d.material_fee)}</td>
            </tr>
            <tr>
                <td class="label-cell" colspan="2">预计收入（元）</td>
                <td colspan="6">${num('estimated_revenue', d.estimated_revenue)}</td>
            </tr>
            <tr>
                <td class="label-cell" colspan="3">合同信息报送确认单</td>
                <td colspan="2" class="text-sm">
                    ${cb('has_contract_info_confirmation', '有', d.has_contract_info_confirmation)}
                    ${cb('has_contract_info_confirmation_no', '无', !d.has_contract_info_confirmation)}
                </td>
            </tr>
            <tr>
                <td class="label-cell writing-vertical" rowspan="2" style="width:40px;">二证一书</td>
                <td class="label-cell" colspan="2">授权书</td>
                <td colspan="2" class="text-sm">
                    ${cb('has_authorization_letter', '有', d.has_authorization_letter)}
                    ${cb('has_authorization_letter_no', '无', !d.has_authorization_letter)}
                </td>
                <td class="label-cell" colspan="2">见证人证书</td>
                <td colspan="2" class="text-sm">
                    ${cb('has_witness_certificate', '有', d.has_witness_certificate)}
                    ${cb('has_witness_certificate_no', '无', !d.has_witness_certificate)}
                </td>
            </tr>
            <tr>
                <td class="label-cell" colspan="2">取样员证书</td>
                <td colspan="2" class="text-sm">
                    ${cb('has_sampler_certificate', '有', d.has_sampler_certificate)}
                    ${cb('has_sampler_certificate_no', '无', !d.has_sampler_certificate)}
                </td>
                <td colspan="5"></td>
            </tr>
            <tr>
                <td class="label-cell writing-vertical" rowspan="4" style="width:28px;">总价预估组成（元）</td>
                <td class="label-cell">地基基础<br>JC0001</td>
                <td>${num('foundation_inspection', d.foundation_inspection)}</td>
                <td class="label-cell">基坑监测<br>JC0005</td>
                <td>${num('foundation_pit_monitoring', d.foundation_pit_monitoring)}</td>
                <td class="label-cell">桥梁检测<br>JC0013</td>
                <td>${num('bridge_inspection', d.bridge_inspection)}</td>
                <td class="label-cell">监督抽检检测<br>JC0027</td>
                <td>${num('supervision_inspection', d.supervision_inspection)}</td>
            </tr>
            <tr>
                <td class="label-cell">材料检测<br>JC0002</td>
                <td>${num('material_inspection', d.material_inspection)}</td>
                <td class="label-cell">环境检测<br>JC0009</td>
                <td>${num('environment_inspection', d.environment_inspection)}</td>
                <td class="label-cell">能效测评<br>JC0010</td>
                <td>${num('energy_efficiency', d.energy_efficiency)}</td>
                <td class="label-cell">防雷检测<br>JC0012</td>
                <td>${num('lightning_protection', d.lightning_protection)}</td>
            </tr>
            <tr>
                <td class="label-cell">房屋评估<br>JC0030</td>
                <td>${num('housing_assessment', d.housing_assessment)}</td>
                <td class="label-cell">结构检测<br>JC0012</td>
                <td>${num('structure_inspection', d.structure_inspection)}</td>
                <td class="label-cell">人防检测<br>JC0014</td>
                <td>${num('civil_defense_inspection', d.civil_defense_inspection)}</td>
                <td class="label-cell">套内质量检测<br>JC0028</td>
                <td>${num('interior_quality', d.interior_quality)}</td>
            </tr>
            <tr>
                <td class="label-cell" colspan="8">
                    <span class="font-bold mr-2">合同盖章内容确认：</span>
                    ${cb('seal_inspection_contract', '检测合同', d.seal_inspection_contract)}
                    ${cb('seal_contract_confirmation', '合同确认单', d.seal_contract_confirmation)}
                    ${cb('seal_integrity_agreement', '廉政协议', d.seal_integrity_agreement)}
                    ${cb('seal_commitment_letter', '承诺函', d.seal_commitment_letter)}
                    ${cb('seal_other', '其他', d.seal_other)}
                    ${txt('seal_other_text', d.seal_other_text)}
                </td>
            </tr>
            <tr>
                <td colspan="5">${signCell('项目承接人', 'project_taker')}</td>
                <td colspan="4">${signCell('项目负责人', 'project_manager')}</td>
            </tr>
            <tr>
                <td colspan="5">${signCell('部门负责人', 'dept_head')}</td>
                <td colspan="4">${signCell('营销管理中心确认', 'marketing')}</td>
            </tr>
            <tr>
                <td colspan="9">
                    <div style="min-height:55px;" class="flex flex-col justify-end">
                        <div class="text-sm mb-1">技术质量管理确认（水利工程）（签名）</div>
                        <div class="flex items-end">
                            <div class="flex-1 border-b border-gray-800 h-8 text-center leading-8">${sigImg('tech_quality')}</div>
                            <div class="ml-2 text-sm whitespace-nowrap">日期：</div>
                            <div class="w-20 border-b border-gray-800 h-8"></div>
                            <div class="ml-4 text-sm whitespace-nowrap">签字确认：</div>
                            <div class="w-24 border-b border-gray-800 h-8"></div>
                        </div>
                    </div>
                </td>
            </tr>
        </table>
        ${readonly ? renderLogs(data) : ""}
    </div>
    `;
}

function renderLogs(data) {
    if (!data.logs || !data.logs.length) return "";
    return `<div class="mt-4">
        <h3 class="font-bold mb-2">审批日志</h3>
        <table class="w-full text-xs border">
            <thead class="bg-gray-50"><tr><th class="border px-2 py-1">时间</th><th class="border px-2 py-1">操作人</th><th class="border px-2 py-1">动作</th><th class="border px-2 py-1">意见</th></tr></thead>
            <tbody>
                ${data.logs.map(l => `<tr>
                    <td class="border px-2 py-1">${formatDate(l.created_at)}</td>
                    <td class="border px-2 py-1">${l.user?.real_name || ""}</td>
                    <td class="border px-2 py-1">${l.action === "approve" ? "通过" : l.action === "reject" ? "驳回" : "提交"}</td>
                    <td class="border px-2 py-1">${l.comment || "-"}</td>
                </tr>`).join("")}
            </tbody>
        </table>
    </div>`;
}

function collectFormData() {
    const form = document.getElementById("contractForm");
    const fd = new FormData(form);
    const get = (name) => fd.get(name) || "";
    const getNum = (name) => parseFloat(fd.get(name) || 0);
    const getBool = (name) => !!fd.get(name);

    let projectCategory = "";
    ["房建","市政基础设施","房屋修缮","轨道交通","水利","民防","公路","绿化","水运","其他"].forEach(x => {
        if (getBool("project_category_" + x)) projectCategory = x;
    });

    let inspectionType = [];
    if (getBool("inspection_type_施工检测")) inspectionType.push("施工检测");
    if (getBool("inspection_type_监理平行检测")) inspectionType.push("监理平行检测");
    if (getBool("inspection_type_监督抽检")) inspectionType.push("监督抽检");
    if (getBool("inspection_type_其他")) inspectionType.push("其他");

    const boolOrNo = (yesName, noName) => {
        const yes = getBool(yesName);
        const no = getBool(noName);
        if (no) return false;
        return yes;
    };

    return {
        business_opportunity_no: get("business_opportunity_no"),
        client_unit: get("client_unit"),
        payer_unit: get("payer_unit"),
        project_name: get("project_name"),
        platform_account: get("platform_account"),
        project_manager_name: get("project_manager_name"),
        project_category: projectCategory,
        project_level: get("project_level"),
        has_approval_document: boolOrNo("has_approval_document", "has_approval_document_no"),
        inspection_type: inspectionType.join(","),
        project_region: get("project_region"),
        has_cooperation_unit: boolOrNo("has_cooperation_unit", "has_cooperation_unit_no"),
        remark: get("remark"),
        construction_cycle_months: getNum("construction_cycle_months") || null,
        estimated_start_date: get("estimated_start_date"),
        actual_start_date: get("actual_start_date"),
        contract_total_price: getNum("contract_total_price"),
        discount_rate: getNum("discount_rate"),
        coordination_fee: getNum("coordination_fee"),
        labor_fee: getNum("labor_fee"),
        material_fee: getNum("material_fee"),
        estimated_revenue: getNum("estimated_revenue"),
        has_contract_info_confirmation: boolOrNo("has_contract_info_confirmation", "has_contract_info_confirmation_no"),
        has_authorization_letter: boolOrNo("has_authorization_letter", "has_authorization_letter_no"),
        has_witness_certificate: boolOrNo("has_witness_certificate", "has_witness_certificate_no"),
        has_sampler_certificate: boolOrNo("has_sampler_certificate", "has_sampler_certificate_no"),
        foundation_inspection: getNum("foundation_inspection"),
        material_inspection: getNum("material_inspection"),
        housing_assessment: getNum("housing_assessment"),
        foundation_pit_monitoring: getNum("foundation_pit_monitoring"),
        environment_inspection: getNum("environment_inspection"),
        structure_inspection: getNum("structure_inspection"),
        bridge_inspection: getNum("bridge_inspection"),
        energy_efficiency: getNum("energy_efficiency"),
        civil_defense_inspection: getNum("civil_defense_inspection"),
        supervision_inspection: getNum("supervision_inspection"),
        lightning_protection: getNum("lightning_protection"),
        interior_quality: getNum("interior_quality"),
        seal_inspection_contract: getBool("seal_inspection_contract"),
        seal_contract_confirmation: getBool("seal_contract_confirmation"),
        seal_integrity_agreement: getBool("seal_integrity_agreement"),
        seal_commitment_letter: getBool("seal_commitment_letter"),
        seal_other: getBool("seal_other"),
        seal_other_text: get("seal_other_text")
    };
}

function renderAttachmentsEditor(formId, attachments) {
    const atts = attachments || [];
    const listHtml = atts.map(a => {
        const displayName = a.split("|")[0];
        const uniqueName = a.split("|")[1];
        return `<div class="flex items-center justify-between bg-gray-50 px-3 py-2 rounded mb-1" data-filename="${escapeHtml(a)}">
            <a href="/uploads/${encodeURIComponent(uniqueName)}" target="_blank" class="text-blue-600 hover:underline text-sm truncate flex-1">${escapeHtml(displayName)}</a>
            ${formId !== "new" ? `<button type="button" class="del-attach text-red-500 text-xs ml-2 hover:underline">删除</button>` : ""}
        </div>`;
    }).join("");

    return `
    <div class="bg-white p-4 rounded shadow mt-4">
        <h3 class="font-bold mb-2 text-sm">附件</h3>
        <div id="attachmentsList" class="mb-2">${listHtml}</div>
        <div class="flex items-center gap-2">
            <input type="file" id="attachFile" class="hidden">
            <button type="button" id="btnAttach" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">+ 上传附件</button>
            <span class="text-xs text-gray-400">支持图片、PDF、Word 等格式</span>
        </div>
    </div>`;
}

async function renderFormEditor(id) {
    let data = {};
    const isNew = id === "new";
    if (!isNew) {
        try { data = await api.getForm(id); } catch (e) { alert(e.message); window.location.hash = "#list"; return; }
    }
    app.innerHTML = `<div class="p-4 max-w-7xl mx-auto">
        <div class="flex items-center justify-between mb-4">
            <h1 class="text-xl font-bold">${isNew ? "新建" : "编辑"}合同流转单</h1>
            <div class="space-x-2">
                <button id="btnOcr" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">📄 上传合同文件识别</button>
                <input type="file" id="ocrFile" class="hidden" accept="image/*,.pdf,.docx,.doc">
                <button id="btnSave" class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700">保存草稿</button>
                <button id="btnSubmit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">提交审批</button>
                <button onclick="location.hash='#list'" class="bg-white border px-4 py-2 rounded hover:bg-gray-50">返回</button>
            </div>
        </div>
        <form id="contractForm">
            ${generateFormHTML(data, false)}
        </form>
        ${renderAttachmentsEditor(id, data.attachments)}
    </div>`;

    // OCR 图片上传
    const btnOcr = document.getElementById("btnOcr");
    const ocrFile = document.getElementById("ocrFile");
    if (btnOcr) {
        btnOcr.addEventListener("click", () => ocrFile.click());
        ocrFile.addEventListener("change", async () => {
            if (!ocrFile.files[0]) return;
            btnOcr.disabled = true;
            btnOcr.textContent = "识别中...";
            try {
                const res = await api.ocrContract(ocrFile.files[0]);
                // 填充识别结果到表单
                if (res.project_name) {
                    const el = document.querySelector('input[name="project_name"]');
                    if (el) el.value = res.project_name;
                }
                if (res.client_unit) {
                    const el = document.querySelector('input[name="client_unit"]');
                    if (el) el.value = res.client_unit;
                }
                if (res.payer_unit) {
                    const el = document.querySelector('input[name="payer_unit"]');
                    if (el) el.value = res.payer_unit;
                }
                let msg = "识别完成";
                if (res.project_name) msg += `\n工程名称: ${res.project_name}`;
                if (res.client_unit) msg += `\n委托单位: ${res.client_unit}`;
                if (res.payer_unit) msg += `\n付款单位: ${res.payer_unit}`;
                alert(msg);
            } catch (e) {
                alert("识别失败: " + e.message);
            } finally {
                btnOcr.disabled = false;
                btnOcr.textContent = "📄 上传合同文件识别";
                ocrFile.value = "";
            }
        });
    }

    document.getElementById("btnSave").addEventListener("click", async () => {
        const payload = collectFormData();
        try {
            if (isNew) {
                const res = await api.createForm(payload);
                alert("保存成功");
                window.location.hash = `#form/${res.id}`;
            } else {
                await api.updateForm(id, payload);
                alert("保存成功");
            }
        } catch (e) { alert(e.message); }
    });

    document.getElementById("btnSubmit").addEventListener("click", async () => {
        const payload = collectFormData();
        try {
            let formId = id;
            if (isNew) {
                const res = await api.createForm(payload);
                formId = res.id;
            } else {
                await api.updateForm(id, payload);
            }
            await api.submitForm(formId);
            alert("提交成功");
            window.location.hash = "#list";
        } catch (e) { alert(e.message); }
    });

    // 附件上传
    const btnAttach = document.getElementById("btnAttach");
    const attachFile = document.getElementById("attachFile");
    if (btnAttach && attachFile) {
        btnAttach.addEventListener("click", () => attachFile.click());
        attachFile.addEventListener("change", async () => {
            if (!attachFile.files[0]) return;
            if (isNew) {
                alert("请先保存表单再上传附件");
                attachFile.value = "";
                return;
            }
            btnAttach.disabled = true;
            btnAttach.textContent = "上传中...";
            try {
                await api.uploadAttachment(id, attachFile.files[0]);
                alert("上传成功");
                // 刷新页面
                window.location.reload();
            } catch (e) {
                alert("上传失败: " + e.message);
            } finally {
                btnAttach.disabled = false;
                btnAttach.textContent = "+ 上传附件";
                attachFile.value = "";
            }
        });
    }

    // 附件删除
    document.querySelectorAll(".del-attach").forEach(btn => {
        btn.addEventListener("click", async () => {
            const filename = btn.closest("[data-filename]").dataset.filename;
            if (!confirm("确定删除此附件？")) return;
            try {
                await api.deleteAttachment(id, filename);
                alert("删除成功");
                window.location.reload();
            } catch (e) {
                alert("删除失败: " + e.message);
            }
        });
    });
}

async function renderFormViewer(id) {
    let data;
    try { data = await api.getForm(id); } catch (e) { alert(e.message); window.location.hash = "#list"; return; }
    app.innerHTML = `<div class="p-4 max-w-7xl mx-auto">
        <div class="flex items-center justify-between mb-4 no-print">
            <h1 class="text-xl font-bold">查看合同流转单</h1>
            <div class="space-x-2">
                ${currentUser.role === "admin" ? `<button onclick="location.hash='#form/${id}'" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">编辑</button>` : ""}
                ${canApprove(data.status) ? `<button onclick="location.hash='#approve/${id}'" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">去审批</button>` : ""}
                <button onclick="location.hash='#pdf/${id}'" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">打印PDF</button>
                <button onclick="location.hash='#list'" class="bg-white border px-4 py-2 rounded hover:bg-gray-50">返回</button>
            </div>
        </div>
        ${generateFormHTML(data, true)}
        ${renderAttachmentsReadOnly(data.attachments)}
    </div>`;
}

async function renderApproval(id) {
    let data;
    try { data = await api.getForm(id); } catch (e) { alert(e.message); window.location.hash = "#list"; return; }
    if (!canApprove(data.status)) {
        alert("当前状态不需要您审批");
        window.location.hash = "#list";
        return;
    }
    const approverRoleMap = {
        pending_manager: "项目负责人",
        pending_dept: "部门负责人",
        pending_marketing: "营销管理中心",
        pending_tech: "技术质量管理"
    };
    const approverLabel = approverRoleMap[data.status] || "审批人";
    const pmDisplay = data.status === "pending_manager" && data.project_manager_name
        ? `<div class="mb-2 text-sm text-gray-700">项目负责人姓名：<span class="font-bold">${escapeHtml(data.project_manager_name)}</span></div>`
        : "";

    app.innerHTML = `<div class="p-4 max-w-7xl mx-auto">
        <div class="flex items-center justify-between mb-4 no-print">
            <h1 class="text-xl font-bold">审批合同流转单</h1>
            <button onclick="location.hash='#list'" class="bg-white border px-4 py-2 rounded hover:bg-gray-50">返回</button>
        </div>
        ${generateFormHTML(data, true)}
        ${renderAttachmentsReadOnly(data.attachments)}
        <div class="bg-white p-6 rounded shadow mt-4 no-print">
            ${pmDisplay}
            <h3 class="font-bold mb-2">${approverLabel}签字</h3>
            <div class="border rounded w-full h-40 relative bg-white" id="sigContainer">
                <canvas id="signaturePad" class="w-full h-full block"></canvas>
            </div>
            <div class="mt-2 flex gap-2">
                <button id="btnClearSig" type="button" class="bg-gray-200 px-3 py-1 rounded text-sm hover:bg-gray-300">清空签名</button>
            </div>
            <div class="mt-4">
                <label class="block text-sm font-medium">审批意见</label>
                <textarea id="comment" rows="2" class="w-full border rounded px-3 py-2 mt-1"></textarea>
            </div>
            <div class="mt-4 flex gap-3">
                <button id="btnApprove" class="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700">通过</button>
                <button id="btnReject" class="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700">驳回</button>
            </div>
        </div>
    </div>`;

    signatureBox = new SignatureBox("signaturePad", "btnClearSig");
    await signatureBox.init();

    document.getElementById("btnApprove").addEventListener("click", async () => {
        if (signatureBox.isEmpty()) { alert("请先手写签名"); return; }
        const sig = signatureBox.toDataURL();
        const comment = document.getElementById("comment").value;
        try {
            await api.approveForm(id, sig, comment);
            alert("审批通过");
            window.location.hash = "#list";
        } catch (e) { alert(e.message); }
    });

    document.getElementById("btnReject").addEventListener("click", async () => {
        const comment = document.getElementById("comment").value;
        try {
            await api.rejectForm(id, comment);
            alert("已驳回");
            window.location.hash = "#list";
        } catch (e) { alert(e.message); }
    });
}

async function renderPdfPreview(id) {
    let data;
    try { data = await api.getForm(id); } catch (e) { alert(e.message); window.location.hash = "#list"; return; }
    app.innerHTML = `<div class="p-4 max-w-7xl mx-auto">
        <div class="flex items-center justify-between mb-4 no-print">
            <h1 class="text-xl font-bold">PDF 预览</h1>
            <div class="space-x-2">
                <button id="btnDownloadPdf" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">下载 PDF</button>
                <button onclick="location.hash='#list'" class="bg-white border px-4 py-2 rounded hover:bg-gray-50">返回</button>
            </div>
        </div>
        <div id="pdfArea" class="bg-white p-6 shadow border" style="min-height:600px; width:100%;">
            ${generateFormHTML(data, true)}
        </div>
    </div>`;
    document.getElementById("btnDownloadPdf").addEventListener("click", () => {
        printPdf("pdfArea", `合同流转单_${data.business_opportunity_no || data.id}.pdf`);
    });
}

init();
