const API_BASE = "";
let token = localStorage.getItem("token") || "";

async function apiFetch(url, options = {}) {
    const headers = {
        "Accept": "application/json",
        ...(options.headers || {})
    };
    if (token && !headers["Authorization"]) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }
    const res = await fetch(API_BASE + url, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem("token");
        token = "";
        window.location.hash = "#login";
        throw new Error("登录已过期");
    }
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "请求失败" }));
        let msg = err.detail || "请求失败";
        if (Array.isArray(msg)) {
            msg = msg.map(x => x.msg || JSON.stringify(x)).join("; ");
        }
        throw new Error(msg);
    }
    if (res.status === 204) return null;
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return await res.json();
    return await res.blob();
}

const api = {
    login: (username, password) => {
        const form = new URLSearchParams();
        form.append("username", username);
        form.append("password", password);
        return apiFetch("/auth/login", { method: "POST", body: form });
    },
    me: () => apiFetch("/auth/me"),
    listForms: (params = "") => apiFetch("/forms" + params),
    getForm: (id) => apiFetch(`/forms/${id}`),
    createForm: (data) => apiFetch("/forms", { method: "POST", body: data }),
    updateForm: (id, data) => apiFetch(`/forms/${id}`, { method: "PUT", body: data }),
    deleteForm: (id) => apiFetch(`/forms/${id}`, { method: "DELETE" }),
    submitForm: (id, comment = "") => apiFetch(`/forms/${id}/submit`, { method: "POST", body: { action: "submit", comment } }),
    approveForm: (id, signatureData, comment = "") => apiFetch(`/forms/${id}/approve`, { method: "POST", body: { action: "approve", signature_data: signatureData, comment } }),
    rejectForm: (id, comment = "") => apiFetch(`/forms/${id}/reject`, { method: "POST", body: { action: "reject", comment } }),
    exportForms: () => apiFetch(`/io/export?t=${Date.now()}`),
    importForms: (file) => {
        const formData = new FormData();
        formData.append("file", file);
        return apiFetch("/io/import", { method: "POST", body: formData });
    },
    ocrContract: (file) => {
        const formData = new FormData();
        formData.append("file", file);
        return apiFetch("/forms/ocr", { method: "POST", body: formData });
    },
    uploadAttachment: (formId, file) => {
        const formData = new FormData();
        formData.append("file", file);
        return apiFetch(`/forms/${formId}/attachments`, { method: "POST", body: formData });
    },
    deleteAttachment: (formId, filename) => {
        return apiFetch(`/forms/${formId}/attachments/${encodeURIComponent(filename)}`, { method: "DELETE" });
    },
    downloadAttachment: (formId, filename) => {
        return apiFetch(`/forms/${formId}/attachments/${encodeURIComponent(filename)}`);
    }
};
