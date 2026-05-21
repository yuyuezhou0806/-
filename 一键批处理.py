"""
一键批处理 - 从原始已盖章 PDF 重新生成最终版

流程:
  原始 PDF (Word 加的小章 + 横切骑缝章)
    ↓ 删旧骑缝章（保留乙方小章）
    ↓ 放大乙方小章（60pt → 130pt）
    ↓ 加新竖向骑缝章（高 18%, 出血 75%）
  最终版 PDF
"""

import os
import io
import sys
import fitz
import shutil
from pathlib import Path
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 骑缝章 import add_riding_seal


SRC_DIR = r"c:/Users/admin/Desktop/合同生成/HT/已生成合同_PDF"
DST_DIR = r"c:/Users/admin/Desktop/合同生成/HT/已生成合同_PDF_最终版"
TMP_DIR = r"c:/Users/admin/Desktop/合同生成/HT/_tmp_处理"
SEAL_PATH = r"c:/Users/admin/Desktop/seal_transparent.png"

YIFANG_SEAL_WIDTH = 130       # 乙方章宽（pt）
RIDING_HEIGHT_RATIO = 0.20    # 骑缝章高度比例
RIDING_VISIBLE_RATIO = 0.8    # 每页切片在页内显示的比例（0.8 = 80% 在页内）


def remove_old_riding_and_enlarge_yifang(src_pdf, mid_pdf, seal_img, new_w):
    """1. 删除旧的横切骑缝章细条
       2. 放大乙方位置的小章
    """
    sw, sh = seal_img.size
    new_h = new_w * sh / sw

    doc = fitz.open(src_pdf)
    yifang_targets = []  # (page_idx, rect)

    for pi, page in enumerate(doc):
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                # 旧横切骑缝章：宽 80-100, 高 5-15, 右侧
                if 80 < r.width < 100 and 5 < r.height < 15 and r.x0 > 400:
                    page.add_redact_annot(r, fill=(1, 1, 1))
                # 乙方小章：宽高 40-90, 不在右边缘
                elif 40 < r.width < 90 and 40 < r.height < 90 and r.x0 < 450:
                    page.add_redact_annot(r, fill=None)
                    yifang_targets.append((pi, r))
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)

    # 在乙方位置插入大章（保持原中心）
    for pi, r in yifang_targets:
        page = doc[pi]
        cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        new_rect = fitz.Rect(cx - new_w/2, cy - new_h/2,
                             cx + new_w/2, cy + new_h/2)
        buf = io.BytesIO()
        seal_img.save(buf, format='PNG')
        buf.seek(0)
        page.insert_image(new_rect, stream=buf.read())

    doc.save(mid_pdf)
    doc.close()
    return len(yifang_targets)


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    seal_img = Image.open(SEAL_PATH).convert("RGBA")

    pdfs = sorted(Path(SRC_DIR).glob("*.pdf"))
    print(f"找到 {len(pdfs)} 个 PDF")
    print(f"输出到: {DST_DIR}\n")

    ok = 0
    fail = []
    for i, pdf in enumerate(pdfs, 1):
        mid = os.path.join(TMP_DIR, pdf.name)
        out = os.path.join(DST_DIR, pdf.name)
        try:
            n_yi = remove_old_riding_and_enlarge_yifang(
                str(pdf), mid, seal_img, YIFANG_SEAL_WIDTH
            )
            success, _ = add_riding_seal(
                mid, SEAL_PATH, out,
                seal_height_ratio=RIDING_HEIGHT_RATIO,
                edge_visible_ratio=RIDING_VISIBLE_RATIO,
            )
            if success:
                ok += 1
                print(f"[{i:>2}/{len(pdfs)}] OK 乙方章×{n_yi} -> {pdf.name}")
        except Exception as e:
            fail.append((pdf.name, str(e)))
            print(f"[{i:>2}/{len(pdfs)}] 失败 {pdf.name}: {e}")

    print(f"\n完成: {ok}/{len(pdfs)} 成功")
    if fail:
        for n, m in fail:
            print(f"  - {n}: {m}")

    # 清临时
    try:
        shutil.rmtree(TMP_DIR)
    except Exception:
        pass


if __name__ == "__main__":
    main()
