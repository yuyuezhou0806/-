"""对报告.pdf 的前 N 页(每页 = 一份独立报告)做 OCR,写到 data/internal_reports_sample.jsonl

每行 = 一份报告:
    {"report_idx": 0, "page_in_pdf": 0, "ocr_text": "..."}

后期需要更多报告类型时,把其他类型的报告 PDF 单独放进 data/internal/reports/ 然后扩展这个脚本。
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PDF = ROOT / "data" / "internal" / "reports" / "报告.pdf"
OUTPUT = ROOT / "data" / "internal_reports_sample.jsonl"

# 采样数量(每页一份报告)
SAMPLE_COUNT = 50

# OCR 分辨率 — 200 dpi 平衡速度和精度
OCR_DPI = 200


def main():
    if not REPORT_PDF.exists():
        print(f"[X] 文件不存在: {REPORT_PDF}")
        sys.exit(1)

    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print("[X] 没装 rapidocr_onnxruntime")
        sys.exit(1)

    print("[*] 加载 OCR 引擎...")
    ocr = RapidOCR()

    print(f"[*] 打开 {REPORT_PDF.name}")
    doc = fitz.open(str(REPORT_PDF))
    total_pages = doc.page_count
    sample_n = min(SAMPLE_COUNT, total_pages)
    print(f"    总 {total_pages} 页, 采样前 {sample_n} 页")

    OUTPUT.parent.mkdir(exist_ok=True, parents=True)
    n_ok, n_empty = 0, 0

    with OUTPUT.open("w", encoding="utf-8") as out:
        for i in range(sample_n):
            page = doc[i]
            pix = page.get_pixmap(dpi=OCR_DPI)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                tmp = f.name
            try:
                pix.save(tmp)
                result, _ = ocr(tmp)
                text = ""
                if result:
                    text = "\n".join(line[1] for line in result).strip()
                if text:
                    n_ok += 1
                else:
                    n_empty += 1
                record = {
                    "report_idx": i,
                    "page_in_pdf": i,
                    "source_file": REPORT_PDF.name,
                    "char_count": len(text),
                    "ocr_text": text,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                # 简单进度
                if (i + 1) % 5 == 0 or i + 1 == sample_n:
                    print(f"  进度: {i + 1}/{sample_n} (有效 {n_ok}, 空 {n_empty})")
            finally:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    doc.close()
    print(f"\n[OK] 写入 {OUTPUT}")
    print(f"     有效 {n_ok} / 空 {n_empty}")


if __name__ == "__main__":
    main()
