function printPdf(elementId, filename = "合同流转确认单.pdf") {
    const element = document.getElementById(elementId);
    if (!element) return;

    // A4 landscape in pixels at 96dpi: 297mm x 210mm
    const PAGE_W = 1122;
    const PAGE_H = 794;

    const elW = element.scrollWidth;
    const elH = element.scrollHeight;

    // Calculate scale to fit everything on one page
    const scale = Math.min(1, PAGE_W / elW, PAGE_H / elH) * 0.96;

    let target = element;
    let wrapper = null;

    if (scale < 1) {
        // Clone element into a hidden wrapper with scale applied
        wrapper = document.createElement("div");
        wrapper.style.position = "absolute";
        wrapper.style.left = "-9999px";
        wrapper.style.top = "0";
        wrapper.style.width = (elW * scale) + "px";
        wrapper.style.height = (elH * scale) + "px";
        wrapper.style.overflow = "hidden";

        const clone = element.cloneNode(true);
        clone.style.transform = `scale(${scale})`;
        clone.style.transformOrigin = "top left";
        clone.style.width = elW + "px";
        clone.style.margin = "0";

        wrapper.appendChild(clone);
        document.body.appendChild(wrapper);
        target = clone;
    }

    const opt = {
        margin: [2, 2, 2, 2],
        filename: filename,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
        jsPDF: { unit: "mm", format: "a4", orientation: "landscape" }
    };

    const cleanup = () => {
        if (wrapper) {
            try { document.body.removeChild(wrapper); } catch (e) {}
        }
    };

    try {
        html2pdf().set(opt).from(target).save().then(cleanup).catch(cleanup);
    } catch (e) {
        cleanup();
    }
}

function getStatusText(status) {
    const map = {
        draft: "草稿",
        pending_manager: "待项目负责人签字",
        pending_dept: "待部门负责人签字",
        pending_marketing: "待营销管理中心确认",
        pending_tech: "待技术质量管理确认",
        approved: "已完成",
        rejected: "已驳回"
    };
    return map[status] || status;
}

function getRoleText(role) {
    const map = {
        project_taker: "项目承接人",
        project_manager: "项目负责人",
        dept_head: "部门负责人",
        marketing: "营销管理中心",
        tech_quality: "技术质量管理",
        admin: "管理员"
    };
    return map[role] || role;
}
