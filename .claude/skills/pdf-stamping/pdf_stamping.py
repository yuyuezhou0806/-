"""
PDF 盖章工具 - 骑缝章 + 乙方公章一体化

功能:
  1. 骑缝章: 把印章按页数沿水平方向切成 N 条竖条,每页右边缘贴一条
             (所有页切片在同一 x 位置,合订后是完整的圆形章)
  2. 乙方章: 检测 PDF 中尺寸较小的小章(原 Word 加的小章)并放大到指定尺寸
             或直接在文本"乙方"附近添加新章

模式:
  - 单文件模式: 选一个 PDF + 印章, 一键盖章
  - 批量模式: 处理整个目录下所有 PDF
"""

import os
import io
import sys
import threading
from pathlib import Path

import fitz
from PIL import Image

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


# ============= 核心算法 =============

def add_riding_seal(doc, seal_img, seal_height_ratio=0.20, edge_visible_ratio=0.80, y_offset=0):
    """
    给 PDF 添加竖向骑缝章 (in-place 修改 doc).

    原理: N 页右边缘同一 x 位置盖印,每页只显示章的一段水平切片,
          叠齐后看上去是一整个章 (真实骑缝章效果).

    Args:
        doc: fitz.Document 对象
        seal_img: PIL.Image, RGBA 印章图
        seal_height_ratio: 章高度占页面高度的比例 (0.20 = 20%)
        edge_visible_ratio: 每页切片在页内显示的比例 (0.8 = 80% 在页内, 20% 出血)
        y_offset: 垂直偏移 (pt)
    """
    page_count = len(doc)
    if page_count < 2:
        return 0

    seal_w, seal_h = seal_img.size
    page_h = doc[0].rect.height
    page_w = doc[0].rect.width

    display_seal_h = page_h * seal_height_ratio
    display_seal_w = seal_w * (display_seal_h / seal_h)
    slice_display_w = display_seal_w / page_count

    slice_x = page_w - slice_display_w * edge_visible_ratio
    slice_y = (page_h - display_seal_h) / 2 + y_offset

    for i in range(page_count):
        page = doc[i]
        left = int(i * seal_w / page_count)
        right = int((i + 1) * seal_w / page_count)
        slice_img = seal_img.crop((left, 0, right, seal_h))

        buf = io.BytesIO()
        slice_img.save(buf, format='PNG')
        buf.seek(0)

        rect = fitz.Rect(slice_x, slice_y,
                         slice_x + slice_display_w, slice_y + display_seal_h)
        page.insert_image(rect, stream=buf.read(), overlay=True)

    return page_count


def remove_old_riding_strips(doc, min_w=80, max_w=100, min_h=5, max_h=15, x_threshold=400):
    """删除右侧细横条(旧错误版骑缝章). in-place"""
    removed = 0
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                if min_w < r.width < max_w and min_h < r.height < max_h and r.x0 > x_threshold:
                    page.add_redact_annot(r, fill=(1, 1, 1))
                    removed += 1
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
    return removed


def enlarge_existing_seals(doc, seal_img, new_width_pt,
                           min_w=40, max_w=90, min_h=40, max_h=90,
                           x_max=450):
    """检测 PDF 中已有的小章并放大替换. in-place

    通过图像尺寸特征识别 (默认: 40-90pt 方形, 不在右边缘)
    """
    sw, sh = seal_img.size
    new_h = new_width_pt * sh / sw

    targets = []
    for pi, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                if (min_w < r.width < max_w and min_h < r.height < max_h
                        and r.x0 < x_max):
                    page.add_redact_annot(r, fill=None)
                    targets.append((pi, r))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)

    for pi, r in targets:
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        rect = fitz.Rect(cx - new_width_pt/2, cy - new_h/2,
                         cx + new_width_pt/2, cy + new_h/2)
        buf = io.BytesIO()
        seal_img.save(buf, format='PNG')
        buf.seek(0)
        doc[pi].insert_image(rect, stream=buf.read(), overlay=True)

    return len(targets)


DEFAULT_SEARCH_PATTERNS = [
    "乙方：（盖章）", "乙方:（盖章）", "乙方(盖章)",
    "盖章：", "盖章:", "（盖章）", "(盖章)",
    "签章", "印章", "乙方盖章",
]


def find_stamp_position(doc, page_num=0, search_text=None):
    """
    在 PDF 中搜索盖章位置.

    Args:
        doc: fitz.Document
        page_num: 0=自动搜索所有页, -1=最后一页, >0=指定页码(1-based)
        search_text: 指定搜索文本, None 则用默认关键词列表

    Returns:
        (page_index, fitz.Rect) 或 (None, None)
    """
    patterns = [search_text] if search_text else DEFAULT_SEARCH_PATTERNS
    page_count = len(doc)

    # 确定搜索范围
    if page_num == -1:
        search_pages = [page_count - 1]
    elif page_num > 0:
        idx = min(page_num - 1, page_count - 1)
        search_pages = [idx]
    else:
        # 自动: 优先搜最后几页(盖章通常在末尾), 找不到再往前
        search_pages = list(range(max(0, page_count - 5), page_count))
        search_pages.reverse()  # 从后往前

    for pi in search_pages:
        page = doc[pi]
        for pat in patterns:
            insts = page.search_for(pat)
            if insts:
                # 取该页最后一处匹配(合同末尾的盖章栏)
                return pi, insts[-1]
    return None, None


def add_yifang_seal_at_text(doc, seal_img, width_pt, page_num=0, search_text=None):
    """
    在文本'盖章'附近添加大章 (用于没有原小章的 PDF). in-place

    Args:
        page_num: 0=自动, -1=最后一页, >0=指定页码
        search_text: 自定义搜索词, None 用默认列表

    返回: dict {'added': int, 'page': int|None, 'keyword': str|None}
    """
    sw, sh = seal_img.size
    new_h = width_pt * sh / sw

    pi, r = find_stamp_position(doc, page_num, search_text)
    if pi is None:
        return {'added': 0, 'page': None, 'keyword': None}

    page = doc[pi]
    # 章中心放在文本右下方,压住"签章"文字的一部分,更像真实盖章
    cx = r.x1 + width_pt * 0.15
    cy = r.y1 + new_h * 0.05
    rect = fitz.Rect(cx - width_pt/2, cy - new_h/2,
                     cx + width_pt/2, cy + new_h/2)
    buf = io.BytesIO()
    seal_img.save(buf, format='PNG')
    buf.seek(0)
    page.insert_image(rect, stream=buf.read(), overlay=True)

    return {'added': 1, 'page': pi + 1, 'keyword': search_text or '默认关键词'}


# ============= 一体化处理 =============

def process_pdf(src_pdf, dst_pdf, seal_path, options):
    """
    完整处理流程.

    options dict:
        remove_old: bool — 是否先删除旧的细条骑缝章
        enlarge_seals: bool — 是否检测并放大已有小章
        yifang_width: float — 乙方章宽 (pt)
        add_riding: bool — 是否加新骑缝章
        riding_height: float — 骑缝章高度比例
        riding_visible: float — 切片在页内显示比例
        riding_offset: int — 骑缝章 y 偏移
        add_yifang_text: bool — 是否通过文本搜索添加乙方章
        yifang_page: int — 0=自动, -1=最后一页, >0=指定页码
        yifang_search_text: str|None — 自定义搜索关键词
    """
    seal_img = Image.open(seal_path).convert("RGBA")
    doc = fitz.open(src_pdf)

    stats = {}
    if options.get("remove_old"):
        stats["removed_old_strips"] = remove_old_riding_strips(doc)

    enlarged = 0
    if options.get("enlarge_seals"):
        enlarged = enlarge_existing_seals(
            doc, seal_img, options.get("yifang_width", 130)
        )
        stats["enlarged_seals"] = enlarged

    # 如果没找到已有小章且开启了文本搜索盖章, 则 fallback
    if options.get("add_yifang_text") and enlarged == 0:
        yf = add_yifang_seal_at_text(
            doc, seal_img, options.get("yifang_width", 130),
            page_num=options.get("yifang_page", 0),
            search_text=options.get("yifang_search_text") or None,
        )
        if yf["added"]:
            stats["yifang_text"] = f"第{yf['page']}页"

    if options.get("add_riding"):
        stats["added_riding"] = add_riding_seal(
            doc, seal_img,
            seal_height_ratio=options.get("riding_height", 0.20),
            edge_visible_ratio=options.get("riding_visible", 0.80),
            y_offset=options.get("riding_offset", 0),
        )

    doc.save(dst_pdf)
    doc.close()
    return stats


# ============= GUI =============

class StampApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF 盖章工具 - 骑缝章 + 乙方章")
        root.geometry("700x750")
        root.resizable(False, False)

        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        # ===== 输入区 =====
        input_frame = ttk.LabelFrame(root, text="文件选择", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(input_frame, text="PDF 文件/文件夹:").grid(row=0, column=0, sticky='w', pady=3)
        self.pdf_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.pdf_var, width=55).grid(row=0, column=1, padx=5)
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=0, column=2)
        ttk.Button(btn_frame, text="文件", width=6, command=self.select_pdf).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="文件夹", width=8, command=self.select_dir).pack(side='left', padx=2)

        ttk.Label(input_frame, text="印章图片:").grid(row=1, column=0, sticky='w', pady=3)
        self.seal_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.seal_var, width=55).grid(row=1, column=1, padx=5)
        ttk.Button(input_frame, text="浏览", width=6, command=self.select_seal).grid(row=1, column=2, padx=2, sticky='w')

        ttk.Label(input_frame, text="输出目录:").grid(row=2, column=0, sticky='w', pady=3)
        self.out_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.out_var, width=55).grid(row=2, column=1, padx=5)
        ttk.Button(input_frame, text="浏览", width=6, command=self.select_out).grid(row=2, column=2, padx=2, sticky='w')

        # ===== 处理选项 =====
        opts_frame = ttk.LabelFrame(root, text="处理选项", padding=10)
        opts_frame.pack(fill='x', padx=10, pady=5)

        self.remove_old_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="删除旧的横切骑缝章 (90×9pt 细条)",
                        variable=self.remove_old_var).grid(row=0, column=0, columnspan=3, sticky='w', pady=2)

        self.enlarge_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="检测并放大原有小公章 (40-90pt → 指定大小)",
                        variable=self.enlarge_var).grid(row=1, column=0, columnspan=3, sticky='w', pady=2)

        ttk.Label(opts_frame, text="    放大后宽度:").grid(row=2, column=0, sticky='w')
        self.yifang_w_var = tk.IntVar(value=130)
        ttk.Spinbox(opts_frame, from_=60, to=200, textvariable=self.yifang_w_var, width=8).grid(row=2, column=1, sticky='w')
        ttk.Label(opts_frame, text="pt (130pt ≈ 4.6cm)").grid(row=2, column=2, sticky='w')

        self.add_text_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="在没有原有小章时, 自动在盖章位置添加乙方章",
                        variable=self.add_text_var,
                        command=self._toggle_text_options).grid(row=3, column=0, columnspan=3, sticky='w', pady=(8, 2))

        # 盖章位置子选项
        self.text_sub_frame = ttk.Frame(opts_frame)
        self.text_sub_frame.grid(row=4, column=0, columnspan=3, sticky='w', padx=(20, 0))

        ttk.Label(self.text_sub_frame, text="页码:").grid(row=0, column=0, sticky='w')
        self.page_mode_var = tk.StringVar(value="自动搜索")
        self.page_combo = ttk.Combobox(self.text_sub_frame, textvariable=self.page_mode_var,
                                        values=["自动搜索", "最后一页", "指定页码"],
                                        width=12, state="readonly")
        self.page_combo.grid(row=0, column=1, sticky='w', padx=2)
        self.page_num_var = tk.IntVar(value=1)
        self.page_num_spin = ttk.Spinbox(self.text_sub_frame, from_=1, to=999,
                                          textvariable=self.page_num_var, width=6)
        self.page_num_spin.grid(row=0, column=2, sticky='w', padx=2)
        self.page_num_spin.configure(state='disabled')
        self.page_combo.bind("<<ComboboxSelected>>", self._on_page_mode_change)

        ttk.Label(self.text_sub_frame, text="搜索词:").grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.search_text_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.text_sub_frame, textvariable=self.search_text_var, width=18)
        self.search_entry.grid(row=1, column=1, columnspan=2, sticky='w', padx=2, pady=(4, 0))
        ttk.Label(self.text_sub_frame, text="(留空=自动识别 盖章/签章/乙方盖章)").grid(
            row=1, column=3, sticky='w', padx=4, pady=(4, 0))

        self._toggle_text_options()

        self.riding_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="添加竖向骑缝章",
                        variable=self.riding_var).grid(row=5, column=0, columnspan=3, sticky='w', pady=(8, 2))

        ttk.Label(opts_frame, text="    章高比例:").grid(row=6, column=0, sticky='w')
        self.height_var = tk.DoubleVar(value=0.20)
        h_scale = ttk.Scale(opts_frame, from_=0.10, to=0.50, variable=self.height_var, orient='horizontal', length=200)
        h_scale.grid(row=6, column=1, sticky='w')
        self.height_label = ttk.Label(opts_frame, text="20%")
        self.height_label.grid(row=6, column=2, sticky='w')
        h_scale.configure(command=lambda v: self.height_label.configure(text=f"{float(v)*100:.0f}%"))

        ttk.Label(opts_frame, text="    切片可见:").grid(row=7, column=0, sticky='w')
        self.visible_var = tk.DoubleVar(value=0.80)
        v_scale = ttk.Scale(opts_frame, from_=0.3, to=1.0, variable=self.visible_var, orient='horizontal', length=200)
        v_scale.grid(row=7, column=1, sticky='w')
        self.visible_label = ttk.Label(opts_frame, text="80%")
        self.visible_label.grid(row=7, column=2, sticky='w')
        v_scale.configure(command=lambda v: self.visible_label.configure(text=f"{float(v)*100:.0f}%"))

        ttk.Label(opts_frame, text="    垂直偏移:").grid(row=8, column=0, sticky='w')
        self.offset_var = tk.IntVar(value=0)
        ttk.Spinbox(opts_frame, from_=-200, to=200, textvariable=self.offset_var, width=8).grid(row=8, column=1, sticky='w')
        ttk.Label(opts_frame, text="pt (正数向下)").grid(row=8, column=2, sticky='w')

        # ===== 开始按钮 =====
        ttk.Button(root, text="开始处理", command=self.start).pack(pady=8)

        # ===== 日志 =====
        ttk.Label(root, text="处理日志:").pack(anchor='w', padx=12)
        self.log = scrolledtext.ScrolledText(root, height=12, font=('Consolas', 9))
        self.log.pack(fill='both', expand=True, padx=10, pady=(0, 5))

        # 推广信息
        promo = tk.Label(root, text="定制 AI 应用软件落地  +v13701758707",
                         font=('Microsoft YaHei', 9), fg='#666666', bg='#f0f0f0')
        promo.pack(fill='x', padx=10, pady=(0, 8))

        self.append_log("就绪. 选择 PDF 文件或文件夹后点击「开始处理」.")

    def append_log(self, msg):
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.root.update_idletasks()

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF 文件", "*.pdf")])
        if path:
            self.pdf_var.set(path)
            if not self.out_var.get():
                self.out_var.set(os.path.dirname(path))

    def select_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.pdf_var.set(path)
            if not self.out_var.get():
                self.out_var.set(path + "_已盖章")

    def select_seal(self):
        path = filedialog.askopenfilename(filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.seal_var.set(path)

    def select_out(self):
        path = filedialog.askdirectory()
        if path:
            self.out_var.set(path)

    def _toggle_text_options(self):
        state = 'normal' if self.add_text_var.get() else 'disabled'
        for child in self.text_sub_frame.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Spinbox, ttk.Combobox)):
                # Spinbox 在 disabled 后需要特殊处理
                pass
            child.configure(state=state)
        # 单独处理控件状态
        mode = self.page_mode_var.get()
        if self.add_text_var.get():
            self.page_combo.configure(state='readonly')
            self.search_entry.configure(state='normal')
            self.page_num_spin.configure(
                state='normal' if mode == '指定页码' else 'disabled'
            )
        else:
            self.page_combo.configure(state='disabled')
            self.search_entry.configure(state='disabled')
            self.page_num_spin.configure(state='disabled')

    def _on_page_mode_change(self, event=None):
        if not self.add_text_var.get():
            return
        mode = self.page_mode_var.get()
        self.page_num_spin.configure(
            state='normal' if mode == '指定页码' else 'disabled'
        )

    def collect_options(self):
        # 页码模式转数值
        mode_map = {'自动搜索': 0, '最后一页': -1, '指定页码': self.page_num_var.get()}
        page_num = mode_map.get(self.page_mode_var.get(), 0)

        return {
            "remove_old": self.remove_old_var.get(),
            "enlarge_seals": self.enlarge_var.get(),
            "yifang_width": self.yifang_w_var.get(),
            "add_riding": self.riding_var.get(),
            "riding_height": self.height_var.get(),
            "riding_visible": self.visible_var.get(),
            "riding_offset": self.offset_var.get(),
            "add_yifang_text": self.add_text_var.get(),
            "yifang_page": page_num,
            "yifang_search_text": self.search_text_var.get().strip() or None,
        }

    def start(self):
        src = self.pdf_var.get().strip()
        seal = self.seal_var.get().strip()
        out_dir = self.out_var.get().strip()

        if not src or not os.path.exists(src):
            messagebox.showerror("错误", "请选择 PDF 文件或文件夹")
            return
        if not seal or not os.path.exists(seal):
            messagebox.showerror("错误", "请选择印章图片")
            return
        if not out_dir:
            messagebox.showerror("错误", "请指定输出目录")
            return

        os.makedirs(out_dir, exist_ok=True)
        options = self.collect_options()

        # 收集 PDF 文件
        if os.path.isfile(src):
            pdfs = [Path(src)]
        else:
            pdfs = sorted(Path(src).glob("*.pdf"))

        if not pdfs:
            messagebox.showerror("错误", "没找到 PDF 文件")
            return

        self.append_log(f"\n===== 开始处理 {len(pdfs)} 个文件 =====")
        threading.Thread(target=self._run, args=(pdfs, out_dir, seal, options), daemon=True).start()

    def _run(self, pdfs, out_dir, seal, options):
        ok = 0
        fail = []
        for i, pdf in enumerate(pdfs, 1):
            out = os.path.join(out_dir, pdf.name)
            # 若输出路径与输入相同, 自动加 _已盖章 后缀避免覆盖
            if os.path.abspath(out) == os.path.abspath(str(pdf)):
                stem, ext = os.path.splitext(pdf.name)
                out = os.path.join(out_dir, f"{stem}_已盖章{ext}")
            try:
                stats = process_pdf(str(pdf), out, seal, options)
                ok += 1
                parts = []
                if "removed_old_strips" in stats:
                    parts.append(f"删旧条×{stats['removed_old_strips']}")
                if "enlarged_seals" in stats:
                    parts.append(f"放大章×{stats['enlarged_seals']}")
                if "yifang_text" in stats:
                    parts.append(f"文本盖章{stats['yifang_text']}")
                if "added_riding" in stats:
                    parts.append(f"骑缝×{stats['added_riding']}")
                self.append_log(f"[{i}/{len(pdfs)}] OK {' '.join(parts)}  -> {os.path.basename(out)}")
            except Exception as e:
                fail.append((pdf.name, str(e)))
                self.append_log(f"[{i}/{len(pdfs)}] 失败 {pdf.name}: {e}")

        self.append_log(f"\n===== 完成 {ok}/{len(pdfs)} =====")
        self.append_log(f"输出目录: {out_dir}")
        if fail:
            self.append_log(f"失败 {len(fail)} 个:")
            for n, m in fail:
                self.append_log(f"  - {n}: {m}")


def main():
    root = tk.Tk()
    StampApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
