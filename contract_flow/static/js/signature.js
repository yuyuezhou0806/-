function loadSignatureScript() {
    return new Promise((resolve, reject) => {
        if (window.SignaturePad) return resolve();
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/signature_pad@4.1.7/dist/signature_pad.umd.min.js";
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

class SignatureBox {
    constructor(canvasId, clearBtnId) {
        this.canvas = document.getElementById(canvasId);
        this.clearBtn = document.getElementById(clearBtnId);
        this.pad = null;
    }

    async init() {
        await loadSignatureScript();
        this.pad = new SignaturePad(this.canvas, {
            backgroundColor: "rgba(255,255,255,1)",
            penColor: "rgb(0,0,0)",
            minWidth: 2,
            maxWidth: 5,
            dotSize: 4
        });
        this.resize();
        window.addEventListener("resize", () => this.resize());
        if (this.clearBtn) {
            this.clearBtn.addEventListener("click", () => this.clear());
        }
    }

    resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        if (this.pad) this.pad.fromData(this.pad.toData());
    }

    clear() {
        if (this.pad) this.pad.clear();
    }

    isEmpty() {
        return this.pad ? this.pad.isEmpty() : true;
    }

    toDataURL() {
        return this.pad ? this.pad.toDataURL("image/png") : "";
    }
}
