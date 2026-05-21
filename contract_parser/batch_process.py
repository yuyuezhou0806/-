import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from extract import extract_pdf_text
from parse_contract import ContractParser, ContractInfo

DB_PATH = "contracts.db"


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            project_name TEXT,
            party_a TEXT,
            party_b TEXT,
            contract_no TEXT,
            amount REAL,
            amount_words TEXT,
            tax_rate REAL,
            tax_amount REAL,
            amount_without_tax REAL,
            sign_date TEXT,
            sign_location TEXT,
            service_content TEXT,  -- JSON array
            address_a TEXT,
            address_b TEXT,
            contact_phone_a TEXT,
            contact_phone_b TEXT,
            bank_b TEXT,
            account_b TEXT,
            confidence INTEGER DEFAULT 0,
            extraction_method TEXT,  -- text / ocr / mixed
            total_pages INTEGER,
            ocr_pages INTEGER,
            status TEXT DEFAULT 'success',  -- success / failed
            error_msg TEXT,
            processed_at TEXT,
            raw_text_preview TEXT
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_contracts_party_a ON contracts(party_a)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_contracts_party_b ON contracts(party_b)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_contracts_project ON contracts(project_name)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_contracts_date ON contracts(sign_date)
    ''')

    conn.commit()
    conn.close()


def process_pdf(pdf_path: str, parser: ContractParser) -> dict:
    """处理单个 PDF，返回结果字典"""
    result = {
        "filepath": pdf_path,
        "filename": os.path.basename(pdf_path),
        "status": "success",
        "error_msg": "",
    }

    try:
        # 1. 提取文本
        extract_result = extract_pdf_text(pdf_path, use_ocr=True)
        result["total_pages"] = extract_result["total_pages"]
        result["ocr_pages"] = extract_result["ocr_pages"]
        result["extraction_method"] = "text" if extract_result["ocr_pages"] == 0 else "ocr"

        # 取前 2000 字作为预览
        raw_text = extract_result["full_text"]
        result["raw_text_preview"] = raw_text[:2000]

        # 2. 解析合同
        info = parser.parse(raw_text)
        result["info"] = info

    except Exception as e:
        result["status"] = "failed"
        result["error_msg"] = str(e)

    return result


def save_to_db(result: dict):
    """保存结果到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    info = result.get("info")
    if info:
        cursor.execute('''
            INSERT INTO contracts (
                filename, filepath, project_name, party_a, party_b,
                contract_no, amount, amount_words, tax_rate, tax_amount,
                amount_without_tax, sign_date, sign_location, service_content,
                address_a, address_b, contact_phone_a, contact_phone_b,
                bank_b, account_b, confidence, extraction_method,
                total_pages, ocr_pages, status, error_msg, processed_at,
                raw_text_preview
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result["filename"],
            result["filepath"],
            info.project_name,
            info.party_a,
            info.party_b,
            info.contract_no,
            info.amount,
            info.amount_words,
            info.tax_rate,
            info.tax_amount,
            info.amount_without_tax,
            info.sign_date,
            info.sign_location,
            json.dumps(info.service_content, ensure_ascii=False),
            info.address_a,
            info.address_b,
            info.contact_phone_a,
            info.contact_phone_b,
            info.bank_b,
            info.account_b,
            info.confidence,
            result.get("extraction_method", ""),
            result.get("total_pages", 0),
            result.get("ocr_pages", 0),
            result["status"],
            result.get("error_msg", ""),
            datetime.now().isoformat(),
            result.get("raw_text_preview", "")
        ))
    else:
        cursor.execute('''
            INSERT INTO contracts (
                filename, filepath, status, error_msg, processed_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            result["filename"],
            result["filepath"],
            result["status"],
            result.get("error_msg", ""),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


def get_stats():
    """获取处理统计"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM contracts')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM contracts WHERE status = "success"')
    success = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM contracts WHERE status = "failed"')
    failed = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM contracts WHERE extraction_method = "ocr"')
    ocr_count = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(confidence) FROM contracts WHERE status = "success"')
    avg_confidence = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "ocr_count": ocr_count,
        "avg_confidence": round(avg_confidence, 2)
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='批量处理合同 PDF')
    parser.add_argument('input_dir', nargs='?', default='C:/Users/admin/Desktop/scan',
                        help='输入目录 (默认: Desktop/scan)')
    parser.add_argument('--limit', type=int, default=0,
                        help='限制处理数量 (0=全部)')
    parser.add_argument('--skip-existing', action='store_true',
                        help='跳过已处理的文件')
    args = parser.parse_args()

    # 初始化
    init_db()
    contract_parser = ContractParser()

    # 收集 PDF 文件
    pdf_files = []
    for root, dirs, files in os.walk(args.input_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, f))

    # 也检查 Desktop 根目录
    desktop_root = 'C:/Users/admin/Desktop'
    for f in os.listdir(desktop_root):
        if f.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(desktop_root, f))

    # 去重并按修改时间排序（最新的先处理）
    pdf_files = list(set(pdf_files))
    pdf_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    if args.limit > 0:
        pdf_files = pdf_files[:args.limit]

    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    print(f"输入目录: {args.input_dir}")
    print("=" * 50)

    # 检查已处理的文件
    if args.skip_existing:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT filepath FROM contracts')
        existing = set(row[0] for row in cursor.fetchall())
        conn.close()
        pdf_files = [f for f in pdf_files if f not in existing]
        print(f"跳过已处理文件，剩余 {len(pdf_files)} 个")

    # 批量处理
    success_count = 0
    failed_count = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {os.path.basename(pdf_path)}")

        result = process_pdf(pdf_path, contract_parser)
        save_to_db(result)

        if result["status"] == "success":
            success_count += 1
            info = result["info"]
            print(f"  confidence: {info.confidence}/10")
            print(f"  project: {info.project_name[:40] if info.project_name else 'N/A'}")
            print(f"  party_a: {info.party_a[:30] if info.party_a else 'N/A'}")
            print(f"  amount: {info.amount:,.0f}" if info.amount > 0 else "  amount: N/A")
            print(f"  method: {result.get('extraction_method', 'N/A')}, pages: {result.get('total_pages', 0)}")
        else:
            failed_count += 1
            print(f"  FAILED: {result.get('error_msg', '')}")

    # 最终统计
    print("\n" + "=" * 50)
    stats = get_stats()
    print(f"处理完成: 成功 {success_count}, 失败 {failed_count}")
    print(f"数据库总计: {stats['total']} 条记录")
    print(f"  - OCR 识别: {stats['ocr_count']} 份")
    print(f"  - 平均置信度: {stats['avg_confidence']}/10")


if __name__ == "__main__":
    main()
