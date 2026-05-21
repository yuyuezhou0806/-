"""
批量放大乙方章
在已经盖好骑缝章的 PDF 上，把原 Word 加的小公章（约 60x55pt）放大到 130pt 重盖
"""

import os
import io
import sys
import fitz
from pathlib import Path
from PIL import Image


SRC_DIR = r"c:/Users/admin/Desktop/合同生成/HT/已生成合同_PDF_新骑缝章"
DST_DIR = r"c:/Users/admin/Desktop/合同生成/HT/已生成合同_PDF_最终版"
SEAL_PATH = r"c:/Users/admin/Desktop/seal_transparent.png"
NEW_SEAL_WIDTH = 130  # pt，约 4.6cm


def enlarge_yifang_seal(src_pdf, dst_pdf, seal_img, new_w):
    """找出乙方位置的小章（非骑缝章），删除后用大章替换"""
    sw, sh = seal_img.size
    new_h = new_w * sh / sw

    doc = fitz.open(src_pdf)
    targets_per_page = []

    for page in doc:
        page_targets = []
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                # 旧 Word 章特征：宽高 40-90、不在右边缘（x0 < 450）、不是骑缝章细条
                if (40 < r.width < 90 and 40 < r.height < 90 and r.x0 < 450):
                    page.add_redact_annot(r, fill=None)
                    page_targets.append(r)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
        targets_per_page.append(page_targets)

    # 重新插入大章（保持原中心）
    total = 0
    for page, targets in zip(doc, targets_per_page):
        for r in targets:
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            new_rect = fitz.Rect(cx - new_w/2, cy - new_h/2,
                                 cx + new_w/2, cy + new_h/2)
            buf = io.BytesIO()
            seal_img.save(buf, format='PNG')
            buf.seek(0)
            page.insert_image(new_rect, stream=buf.read())
            total += 1

    doc.save(dst_pdf)
    doc.close()
    return total


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    seal_img = Image.open(SEAL_PATH).convert("RGBA")

    pdfs = sorted(Path(SRC_DIR).glob("*.pdf"))
    print(f"找到 {len(pdfs)} 个 PDF")
    print(f"输出目录: {DST_DIR}\n")

    ok = 0
    fail = []
    for i, pdf in enumerate(pdfs, 1):
        out = os.path.join(DST_DIR, pdf.name)
        try:
            n = enlarge_yifang_seal(str(pdf), out, seal_img, NEW_SEAL_WIDTH)
            ok += 1
            print(f"[{i:>2}/{len(pdfs)}] OK 替换 {n} 个乙方章 -> {pdf.name}")
        except Exception as e:
            fail.append((pdf.name, str(e)))
            print(f"[{i:>2}/{len(pdfs)}] 失败 {pdf.name}: {e}")

    print(f"\n完成: {ok}/{len(pdfs)} 成功")
    if fail:
        print("失败列表:")
        for n, m in fail:
            print(f"  - {n}: {m}")


if __name__ == "__main__":
    main()
