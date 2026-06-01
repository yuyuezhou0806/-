"""
合同生成器 GUI 入口
- 双击 → 弹文件选择框选图片 → 自动生成合同
- 拖图到 exe → 自动处理
- 命令行: 合同生成器.exe <图片路径>

合同输出到图片所在目录,文件名"<工程名>-已填充.doc"
模板必须放在 exe 同目录,名字"空白合同(房建)2021版.doc"
"""

# ===== monkey patch paddlex deps 预检 =====
# PyInstaller 打包后 importlib.metadata 找不到部分依赖包的 .dist-info,
# paddlex 的 require_extra() 会误判依赖缺失;实际 OCR 核心流程并不需要那些包。
# 在 import paddleocr 之前 patch 掉,让 paddlex 直接跳过预检。
try:
    import paddlex.utils.deps as _deps
    _deps.require_extra = lambda *a, **kw: None
    _deps.is_extra_available = lambda *a, **kw: True
    _deps.is_dep_available = lambda *a, **kw: True
except Exception:
    pass

import os
import re
import sys
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

import contract_filler_ocr as cf


def get_base_dir() -> Path:
    """exe 同目录(打包后) 或 脚本同目录(开发)"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


# 模板候选名(用户文件夹可能有几种命名)
TEMPLATE_CANDIDATES = [
    "空白合同(房建)2021版.doc",
    "空白合同(房建)2021版.doc",
    "空白合同[房建](2021版).doc",
    "空白合同【房建】(2021版).doc",
    "空白合同【房建】(2021版).doc",
]


def find_template(base_dir):
    # 优先找候选名
    for name in TEMPLATE_CANDIDATES:
        p = base_dir / name
        if p.exists():
            return p
    # 兜底:目录里任何 "空白合同" 开头的 .doc/.docx
    for p in base_dir.glob("空白合同*.doc*"):
        return p
    return None


def safe_name(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", s)[:80] or "合同"


def process(image_path, template):
    """走完整流程:OCR → 提取字段 → 填充合同。返回输出路径(在模板同目录)。"""
    image_path = Path(image_path).resolve()
    full_text, texts = cf.ocr_image(str(image_path))

    fields = cf.extract_fields(full_text)
    if not fields:
        raise RuntimeError("OCR 识别成功,但未能从图片中提取到任何字段。请确认截图是上海市建设工程项目信息报送系统的页面。")

    project_name = fields.get("工程名称", "合同")
    output_name = f"{safe_name(project_name)}-已填充.doc"

    config = cf.build_contract_config(fields, str(template), output_name)
    cf.fill_contract(config)

    # fill_contract 会把输出放在 template_dir/output_name
    output_path = Path(template).parent / output_name
    return output_path, fields


def main():
    root = tk.Tk()
    root.withdraw()  # 主窗口不显示,只用对话框

    base_dir = get_base_dir()

    # 命令行参数 = 拖拽路径
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = filedialog.askopenfilename(
            title="选择项目网页截图",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp *.gif"), ("所有文件", "*.*")],
        )
        if not image_path:
            return  # 用户取消

    image_path = Path(image_path)
    if not image_path.exists():
        messagebox.showerror("文件不存在", f"找不到图片:\n{image_path}")
        return

    template = find_template(base_dir)
    if template is None:
        messagebox.showerror(
            "缺少合同模板",
            f"在 exe 所在目录找不到「空白合同(房建)2021版.doc」。\n\n"
            f"请把模板文件放到这里:\n{base_dir}",
        )
        return

    try:
        output_path, fields = process(image_path, template)
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror(
            "生成失败",
            f"出错了:\n{e}\n\n详细错误已打印到命令行(如果可见)。",
        )
        return

    # 成功 - 提示并问要不要打开输出目录
    field_summary = "\n".join(f"  {k}: {v}" for k, v in list(fields.items())[:6])
    ans = messagebox.askyesno(
        "生成成功",
        f"合同已生成:\n{output_path}\n\n"
        f"识别到的字段(前 6 个):\n{field_summary}\n\n"
        f"打开文件所在文件夹?",
    )
    if ans:
        os.startfile(output_path.parent)


if __name__ == "__main__":
    main()
