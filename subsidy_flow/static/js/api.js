const API_BASE = '';

function getToken() {
    return localStorage.getItem('token') || '';
}

async function api(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const resp = await fetch(API_BASE + url, {
        ...options,
        headers,
    });
    if (resp.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(err.detail || '请求失败');
    }
    if (resp.status === 204) return null;
    return resp.json();
}

const apiClient = {
    // Auth
    login: (username, password) => {
        const form = new URLSearchParams();
        form.append('username', username);
        form.append('password', password);
        return fetch(API_BASE + '/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form,
        }).then(r => {
            if (!r.ok) throw new Error('登录失败');
            return r.json();
        });
    },
    me: () => api('/auth/me'),

    // Public
    calculate: (data) => api('/public/calculate', { method: 'POST', body: JSON.stringify(data) }),
    checkCompliance: (data) => api('/public/check-compliance', { method: 'POST', body: JSON.stringify(data) }),
    policySummary: () => api('/public/policy-summary'),
    deadlineCountdown: () => api('/public/deadline-countdown'),
    industries: () => api('/public/industries'),

    // Clients
    listClients: (params = '') => api('/clients' + (params ? '?' + params : '')),
    createClient: (data) => api('/clients', { method: 'POST', body: JSON.stringify(data) }),
    getClient: (id) => api(`/clients/${id}`),
    updateClient: (id, data) => api(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteClient: (id) => api(`/clients/${id}`, { method: 'DELETE' }),

    // Projects
    listProjects: (params = '') => api('/projects' + (params ? '?' + params : '')),
    createProject: (data) => api('/projects', { method: 'POST', body: JSON.stringify(data) }),
    getProject: (id) => api(`/projects/${id}`),
    updateProject: (id, data) => api(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteProject: (id) => api(`/projects/${id}`, { method: 'DELETE' }),
    transitionProject: (id, data) => api(`/projects/${id}/transition`, { method: 'POST', body: JSON.stringify(data) }),
    uploadAttachment: (id, file) => {
        const form = new FormData();
        form.append('file', file);
        return api(`/projects/${id}/attachments`, { method: 'POST', body: form, headers: {} });
    },
    deleteAttachment: (pid, filename) => api(`/projects/${pid}/attachments/${filename}`, { method: 'DELETE' }),

    // Expenses
    listExpenses: (projectId) => api(`/expenses/project/${projectId}`),
    createExpense: (projectId, data) => api(`/expenses/project/${projectId}`, { method: 'POST', body: JSON.stringify(data) }),
    updateExpense: (id, data) => api(`/expenses/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteExpense: (id) => api(`/expenses/${id}`, { method: 'DELETE' }),

    // Reports
    dashboard: () => api('/reports/dashboard'),
};
