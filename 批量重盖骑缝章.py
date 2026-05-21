"""
批量重盖骑缝章
1. 输入目录里所有 PDF
2. 先把旧的"横切骑缝章"（每页中部 ~92x9 的细横条）擦掉
3. 用新算法重新盖竖向骑缝章
4. 输出到指定目录
"""

import os
import sys
import fitz
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 骑缝章 import add_riding_seal


SRC_DIR = r"c:/Users/admin/Desktop/合同生成/HT/已生成合同_PDF"
DST_DIR = r"c:/Users/admin/Desktop/合同生成/HT/已生成合同_PDF_新骑缝章"
TMP_DIR = r"c:/Users/admin/Desktop/合同生成/HT/_tmp_去章"
SEAL_PATH = r"c:/Users/admin/Desktop/seal_transparent.png"


def remove_old_riding_seal(src_pdf, dst_pdf):
    """删除旧骑缝章：右侧、宽 80-100、高 5-15 的细横条"""
    doc = fitz.open(src_pdf)
    removed = 0
    for page in doc:
        imgs = page.get_images(full=True)
        for img in imgs:
            xref = img[0]
            for r in page.get_image_rects(xref):
                if 80 < r.width < 100 and 5 < r.height < 15 and r.x0 > 400:
                    page.add_redact_annot(r, fill=(1, 1, 1))
                    removed += 1
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
    doc.save(dst_pdf)
    doc.close()
    return removed


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)

    pdfs = sorted(Path(SRC_DIR).glob("*.pdf"))
    print(f"找到 {len(pdfs)} 个 PDF")
    print(f"输出目录: {DST_DIR}\n")

    ok_count = 0
    fail = []

    for i, pdf in enumerate(pdfs, 1):
        name = pdf.name
        tmp_path = os.path.join(TMP_DIR, name)
        out_path = os.path.join(DST_DIR, name)
        try:
            removed = remove_old_riding_seal(str(pdf), tmp_path)
            success, msg = add_riding_seal(tmp_path, SEAL_PATH, out_path)
            if success:
                ok_count += 1
                print(f"[{i:>2}/{len(pdfs)}] OK  去除旧切片 {removed}  -> {name}")
            else:
                fail.append((name, msg))
                print(f"[{i:>2}/{len(pdfs)}] 失败 {name}: {msg}")
        except Exception as e:
            fail.append((name, str(e)))
            print(f"[{i:>2}/{len(pdfs)}] 异常 {name}: {e}")

    print(f"\n完成: {ok_count}/{len(pdfs)} 成功")
    if fail:
        print(f"失败 {len(fail)} 个:")
        for n, m in fail:
            print(f"  - {n}: {m}")

    # 清理临时目录
    try:
        for f in Path(TMP_DIR).glob("*"):
            f.unlink()
        os.rmdir(TMP_DIR)
    except Exception:
        pass


if __name__ == "__main__":
    main()
