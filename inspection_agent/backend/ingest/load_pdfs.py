"""把 data/standards/ 下的 PDF 提取成纯文本,写到 data/raw_text.jsonl。

每行一个 JSON:
    {"name": "GB50204-2015", "pages": [{"page": 1, "text": "..."}, ...]}

文字版 PDF 直接用 PyMuPDF 抽;
扫描版(用 PyMuPDF 抽出来是空的)走 RapidOCR 兜底。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "standards"
OUTPUT = ROOT / "data" / "raw_text.jsonl"

# OCR 阈值:单页字符数低于这个值就认为是扫描版,走 OCR
OCR_TRIGGER_CHARS = 20


_ocr = None


def get_ocr():
    """懒加载 RapidOCR(只在真有扫描页时初始化)"""
    global _ocr
    if _ocr is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            print("[!] 没装 rapidocr_onnxruntime,扫描页将跳过")
            return None
        print("[*] 加载 OCR 引擎...")
        _ocr = RapidOCR()
    return _ocr


def ocr_page_image(pix) -> str:
    """对一页的渲染图跑 OCR"""
    ocr = get_ocr()
    if ocr is None:
        return ""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        pix.save(tmp)
        result, _ = ocr(tmp)
        if not result:
            return ""
        return "\n".join(line[1] for line in result)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def extract_pdf(pdf_path: Path) -> dict:
    """一个 PDF → {name, pages: [...]}"""
    doc = fitz.open(str(pdf_path))
    pages = []
    ocr_pages = 0
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if len(text) < OCR_TRIGGER_CHARS:
            # 走 OCR
            pix = page.get_pixmap(dpi=200)
            text = ocr_page_image(pix).strip()
            if text:
                ocr_pages += 1
        if text:
            pages.append({"page": i + 1, "text": text})
    doc.close()
    return {
        "name": pdf_path.stem,
        "source_path": str(pdf_path.relative_to(ROOT)),
        "pages": pages,
        "ocr_pages": ocr_pages,
    }


def main():
    if not DATA_DIR.exists():
        print(f"[X] 数据目录不存在: {DATA_DIR}")
        sys.exit(1)

    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[!] {DATA_DIR} 下没有 PDF。先按 docs/数据准备清单.md 准备数据。")
        sys.exit(1)

    print(f"[*] 发现 {len(pdfs)} 个 PDF")
    OUTPUT.parent.mkdir(exist_ok=True, parents=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for p in pdfs:
            print(f"  解析 {p.name} ...", end=" ", flush=True)
            try:
                data = extract_pdf(p)
            except Exception as e:
                print(f"[X] 失败: {e}")
                continue
            n_pages = len(data["pages"])
            n_ocr = data["ocr_pages"]
            print(f"OK ({n_pages} 页, 其中 OCR {n_ocr} 页)")
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"\n[OK] 写入 {OUTPUT}")
    print(f"     下一步: chunk.py 切段")


if __name__ == "__main__":
    main()
