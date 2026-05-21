import fitz
import os
import json
from pathlib import Path
from typing import Optional, List

# 尝试导入 OCR，未安装则跳过
try:
    from rapidocr_onnxruntime import RapidOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def ocr_page(page: fitz.Page, engine: Optional['RapidOCR'] = None) -> str:
    """对单页 PDF 进行 OCR 识别"""
    if not OCR_AVAILABLE:
        return ""

    if engine is None:
        engine = RapidOCR()

    # PDF 转图片，2x 放大提高识别率
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)

    # 保存临时图片
    tmp_path = f"_tmp_ocr_{page.number}.png"
    pix.save(tmp_path)

    try:
        result, _ = engine(tmp_path)
        texts = [item[1] for item in result]
        return "\n".join(texts)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def extract_pdf_text(pdf_path: str, use_ocr: bool = True, min_text_length: int = 100) -> dict:
    """
    提取 PDF 文本内容
    - 优先提取内嵌文本
    - 文本过少时自动 fallback 到 OCR
    """
    doc = fitz.open(pdf_path)
    pages_text = []
    full_text = ""

    ocr_engine = None
    if use_ocr and OCR_AVAILABLE:
        ocr_engine = RapidOCR()

    for i, page in enumerate(doc):
        text = page.get_text()
        extraction_method = "text"

        # 如果文本太少，尝试 OCR
        if len(text) < min_text_length and use_ocr and OCR_AVAILABLE:
            ocr_text = ocr_page(page, ocr_engine)
            if len(ocr_text) > len(text):
                text = ocr_text
                extraction_method = "ocr"

        page_info = {
            "page": i + 1,
            "text": text,
            "length": len(text),
            "method": extraction_method
        }
        pages_text.append(page_info)
        full_text += f"\n--- 第{i+1}页({extraction_method}) ---\n{text}"

    total_pages = len(doc)
    doc.close()

    # 统计
    ocr_pages = sum(1 for p in pages_text if p["method"] == "ocr")

    return {
        "filename": os.path.basename(pdf_path),
        "total_pages": total_pages,
        "ocr_pages": ocr_pages,
        "full_text": full_text,
        "pages": pages_text
    }


def clean_text(text: str) -> str:
    """清理 PDF 提取的文本，处理竖排/稀疏排版/OCR 噪声"""
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 跳过扫描软件水印
        if '扫描全能王' in line or '亿人都在用的扫描App' in line:
            continue
        if 'CamScanner' in line:
            continue
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def main():
    import sys

    if len(sys.argv) < 2:
        print("usage:")
        print("  python extract.py <PDF file>         # extract with auto OCR fallback")
        print("  python extract.py <PDF file> --text  # text only, no OCR")
        sys.exit(1)

    pdf_path = sys.argv[1]
    use_ocr = "--text" not in sys.argv

    if not os.path.exists(pdf_path):
        print(f"file not found: {pdf_path}")
        sys.exit(1)

    if use_ocr and not OCR_AVAILABLE:
        print("warning: rapidocr not installed, falling back to text extraction only")
        print("install: pip install rapidocr_onnxruntime")
        use_ocr = False

    result = extract_pdf_text(pdf_path, use_ocr=use_ocr)

    # save raw text
    output_dir = Path("extracted")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{Path(pdf_path).stem}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result["full_text"])

    print(f"[OK] extracted: {result['filename']}")
    print(f"  pages: {result['total_pages']}")
    print(f"  OCR pages: {result['ocr_pages']}")
    print(f"  total chars: {len(result['full_text'])}")
    print(f"  saved: {output_file}")

    # cleaned text
    cleaned = clean_text(result["full_text"])
    cleaned_file = output_dir / f"{Path(pdf_path).stem}_cleaned.txt"
    with open(cleaned_file, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    print(f"  cleaned: {cleaned_file}")


if __name__ == "__main__":
    main()
