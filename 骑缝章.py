"""
PDF 电子骑缝章工具
功能：将印章图片按页数沿水平方向切成竖条，每页右边缘贴一条，
合订后全部页面拼起来是一个完整的印章（真实骑缝章效果）
"""

import fitz
from PIL import Image
import io
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def add_riding_seal(pdf_path, seal_path, output_path, seal_height_ratio=0.18, edge_visible_ratio=0.5, y_offset=0):
    """
    给PDF添加电子骑缝章

    原理：模拟真实骑缝章——将 N 张纸叠在一起后边缘错开盖章，
    每页右边缘都印有章的一小段（同一 y 位置、同一 x 位置贴边），
    但每页显示的是章的不同水平切片：第 1 页显示章最左段，
    第 N 页显示章最右段。

    Args:
        pdf_path: 输入PDF路径
        seal_path: 印章图片路径（推荐PNG透明背景）
        output_path: 输出PDF路径
        seal_height_ratio: 印章高度占页面高度的比例
        edge_visible_ratio: 每页章切片显示宽度占切片自身的比例（0~1）
                            =1 表示切片完整显示在页内
                            <1 表示切片有一部分超出页面右边缘
        y_offset: 垂直偏移
    """
    doc = fitz.open(pdf_path)
    page_count = len(doc)

    if page_count < 2:
        doc.save(output_path)
        doc.close()
        return True, "PDF只有1页，直接复制输出"

    seal_img = Image.open(seal_path).convert("RGBA")
    seal_w, seal_h = seal_img.size

    first_page = doc[0]
    page_h = first_page.rect.height
    page_w = first_page.rect.width

    # 印章在页面上的显示总尺寸
    display_seal_h = page_h * seal_height_ratio
    display_seal_w = seal_w * (display_seal_h / seal_h)
    # 每条切片在页面上的宽度
    slice_display_w = display_seal_w / page_count

    # 所有页面的切片都贴在右边缘（同一 x 位置）
    # edge_visible_ratio=0.5 → 切片一半在页内、一半在页外
    slice_x = page_w - slice_display_w * edge_visible_ratio
    # 垂直居中
    slice_y = (page_h - display_seal_h) / 2 + y_offset

    for i in range(page_count):
        page = doc[i]

        # 从印章原图沿水平方向切出第 i 条竖条
        left = int(i * seal_w / page_count)
        right = int((i + 1) * seal_w / page_count)
        slice_img = seal_img.crop((left, 0, right, seal_h))

        img_bytes = io.BytesIO()
        slice_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        img_rect = fitz.Rect(slice_x, slice_y,
                             slice_x + slice_display_w, slice_y + display_seal_h)
        page.insert_image(img_rect, stream=img_bytes.read())

    doc.save(output_path)
    doc.close()
    return True, f"完成！共 {page_count} 页，已保存至:\n{output_path}"


class RidingSealApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 电子骑缝章工具")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        # 样式
        style = ttk.Style()
        style.configure('TButton', font=('Microsoft YaHei', 10))
        style.configure('TLabel', font=('Microsoft YaHei', 10))

        # PDF文件选择
        ttk.Label(root, text="PDF 合同文件:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.pdf_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.pdf_var, width=40).grid(row=0, column=1, padx=5, pady=10)
        ttk.Button(root, text="浏览", command=self.select_pdf).grid(row=0, column=2, padx=5, pady=10)

        # 印章图片选择
        ttk.Label(root, text="印章图片 (PNG):").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.seal_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.seal_var, width=40).grid(row=1, column=1, padx=5, pady=10)
        ttk.Button(root, text="浏览", command=self.select_seal).grid(row=1, column=2, padx=5, pady=10)

        # 参数设置
        param_frame = ttk.LabelFrame(root, text="参数设置", padding=10)
        param_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky='ew')

        ttk.Label(param_frame, text="印章大小:").grid(row=0, column=0, sticky='w')
        self.scale_var = tk.DoubleVar(value=0.18)
        scale_scale = ttk.Scale(param_frame, from_=0.10, to=0.60, variable=self.scale_var, orient='horizontal', length=200)
        scale_scale.grid(row=0, column=1, padx=5)
        self.scale_label = ttk.Label(param_frame, text="18%")
        self.scale_label.grid(row=0, column=2, padx=5)
        scale_scale.configure(command=self.update_scale_label)

        ttk.Label(param_frame, text="切片显示比例:").grid(row=1, column=0, sticky='w', pady=5)
        self.overflow_var = tk.DoubleVar(value=0.5)
        overflow_scale = ttk.Scale(param_frame, from_=0.2, to=1.0, variable=self.overflow_var, orient='horizontal', length=200)
        overflow_scale.grid(row=1, column=1, padx=5, pady=5)
        self.overflow_label = ttk.Label(param_frame, text="50%")
        self.overflow_label.grid(row=1, column=2, padx=5)
        overflow_scale.configure(command=self.update_overflow_label)

        ttk.Label(param_frame, text="垂直偏移:").grid(row=2, column=0, sticky='w')
        self.offset_var = tk.IntVar(value=0)
        ttk.Spinbox(param_frame, from_=-200, to=200, textvariable=self.offset_var, width=8).grid(row=2, column=1, sticky='w')
        ttk.Label(param_frame, text="像素（正数向下）").grid(row=2, column=2, sticky='w')

        # 开始按钮
        ttk.Button(root, text="生成骑缝章 PDF", command=self.process).grid(row=3, column=0, columnspan=3, pady=15)

        # 状态显示
        self.status_var = tk.StringVar(value="请选择PDF文件和印章图片")
        status_label = ttk.Label(root, textvariable=self.status_var, wraplength=480, foreground='gray')
        status_label.grid(row=4, column=0, columnspan=3, padx=10, pady=5)

        # 说明文字
        info_text = """说明：
1. 印章图片建议使用PNG格式（透明背景效果更佳）
2. 输出文件默认保存在PDF同目录，文件名加"_骑缝章"后缀
3. 印章大小建议 25%-35%（占页面高度）
4. 出血量 = 印章超出页面右边缘的比例，50% 表示一半印章在页外，
   模拟真实骑缝章装订效果。要完整显示在页内可设为 0"""
        ttk.Label(root, text=info_text, wraplength=480, foreground='gray', justify='left').grid(
            row=5, column=0, columnspan=3, padx=15, pady=5, sticky='w')

    def update_scale_label(self, val):
        self.scale_label.configure(text=f"{float(val)*100:.0f}%")

    def update_overflow_label(self, val):
        self.overflow_label.configure(text=f"{float(val)*100:.0f}%")

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF文件", "*.pdf")])
        if path:
            self.pdf_var.set(path)
            self.status_var.set(f"已选择PDF: {os.path.basename(path)}")

    def select_seal(self):
        path = filedialog.askopenfilename(filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.seal_var.set(path)
            self.status_var.set(f"已选择印章: {os.path.basename(path)}")

    def process(self):
        pdf_path = self.pdf_var.get()
        seal_path = self.seal_var.get()

        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("错误", "请选择有效的PDF文件")
            return
        if not seal_path or not os.path.exists(seal_path):
            messagebox.showerror("错误", "请选择有效的印章图片")
            return

        # 生成输出路径
        base, ext = os.path.splitext(pdf_path)
        output_path = base + "_骑缝章" + ext

        self.status_var.set("处理中，请稍候...")
        self.root.update()

        try:
            success, msg = add_riding_seal(
                pdf_path,
                seal_path,
                output_path,
                seal_height_ratio=self.scale_var.get(),
                edge_visible_ratio=self.overflow_var.get(),
                y_offset=self.offset_var.get()
            )
            if success:
                messagebox.showinfo("完成", msg)
                self.status_var.set("处理完成")
            else:
                messagebox.showerror("错误", msg)
        except Exception as e:
            messagebox.showerror("错误", f"处理失败:\n{str(e)}")
            self.status_var.set(f"处理失败: {str(e)}")


def main():
    root = tk.Tk()
    app = RidingSealApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
