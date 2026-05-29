"""快速 OCR 报告 PDF 的若干页,了解结构。

只 OCR 指定页(不是全本),用来判断:
- 单份报告大约多少页
- 是否有固定标题/页眉(可以做规则拆分)
- 内容质量
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import fitz
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PDF = ROOT / "data" / "internal" / "reports" / "报告.pdf"

# 要采样的页(0-indexed)
SAMPLE_PAGES = [0, 1, 2, 3, 4, 5, 10, 50, 100, 500, 1000, 1500]


def main():
    if not REPORT_PDF.exists():
        print(f"[X] 文件不存在: {REPORT_PDF}")
        sys.exit(1)

    print("[*] 加载 OCR 引擎...")
    ocr = RapidOCR()

    print(f"[*] 打开 {REPORT_PDF.name}")
    doc = fitz.open(str(REPORT_PDF))
    print(f"    共 {doc.page_count} 页\n")

    for p_idx in SAMPLE_PAGES:
        if p_idx >= doc.page_count:
            continue
        page = doc[p_idx]
        pix = page.get_pixmap(dpi=200)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            pix.save(tmp)
            result, _ = ocr(tmp)
            if not result:
                print(f"=== p.{p_idx} === (OCR 无输出)\n")
                continue
            text = "\n".join(line[1] for line in result)
            # 截前 400 字符够看结构
            preview = text[:400]
            print(f"=== p.{p_idx} ({len(text)} 字) ===")
            print(preview)
            print()
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    doc.close()


if __name__ == "__main__":
    main()
