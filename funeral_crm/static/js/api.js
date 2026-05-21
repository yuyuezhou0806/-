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
    listDeceased: (params = '') => api('/deceased' + (params ? '?' + params : '')),
    createDeceased: (data) => api('/deceased', { method: 'POST', body: JSON.stringify(data) }),
    getDeceased: (id) => api(`/deceased/${id}`),
    updateDeceased: (id, data) => api(`/deceased/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteDeceased: (id) => api(`/deceased/${id}`, { method: 'DELETE' }),
};
