"""把所有原始抽取数据切成 chunks,写到 data/chunks.jsonl

输入:
  data/raw_text.jsonl                  规范条款(Tier 1)
  data/internal_text.jsonl             合同 / 费率表(Tier 2)
  data/internal_reports_sample.jsonl   报告样本(Tier 2)

输出:
  data/chunks.jsonl                    每行一个 chunk

切分策略:
  规范:按 X.Y.Z 条款号切,大块再按长度拆
  合同:按"第X条"切,落空则按长度切
  费率表/Excel:整体切大块(表格语义不能切碎)
  报告:每页 = 一份独立报告 = 一个 chunk
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"

STANDARDS_RAW = DATA_DIR / "raw_text.jsonl"
INTERNAL_RAW = DATA_DIR / "internal_text.jsonl"
REPORTS_RAW = DATA_DIR / "internal_reports_sample.jsonl"
CHUNKS_OUT = DATA_DIR / "chunks.jsonl"

# Chunk size
MIN_CHUNK_CHARS = 50
MAX_CHUNK_CHARS = 1500

# 中文规范条款号(行首,如 3.1.1 / 4.0.5)
CLAUSE_PATTERN = re.compile(
    r"(?m)^[\s　]*(\d+(?:\.\d+){1,4})[\s　]+",
    re.MULTILINE,
)
# 合同条款标记(第一条 / 第二条 / 第十条)
CONTRACT_ARTICLE = re.compile(r"第\s*[一二三四五六七八九十百千零〇\d]+\s*条")


def _split_by_length(text: str, max_chars: int):
    """超长文本按长度切,优先在换行/句号断"""
    if len(text) <= max_chars:
        return [text]
    out = []
    pos = 0
    while pos < len(text):
        end = min(pos + max_chars, len(text))
        if end < len(text):
            for cut in ("\n\n", "\n", "。", ";", ","):
                idx = text.rfind(cut, pos + max_chars // 2, end)
                if idx != -1:
                    end = idx + len(cut)
                    break
        chunk = text[pos:end].strip()
        if chunk:
            out.append(chunk)
        pos = end
    return out


def chunk_standard(doc: dict):
    name = doc["name"]
    pages = doc.get("pages", [])

    # 拼全文 + 页号映射
    full_parts = []
    page_for_pos = []
    for p in pages:
        full_parts.append(p["text"])
        # +1 for the \n separator
        page_for_pos.extend([p["page"]] * (len(p["text"]) + 1))
    full_text = "\n".join(full_parts)

    matches = list(CLAUSE_PATTERN.finditer(full_text))
    chunks = []

    if len(matches) < 3:
        # 找不到清晰条款,按长度切
        for ci, sub in enumerate(_split_by_length(full_text, MAX_CHUNK_CHARS)):
            chunks.append({
                "id": f"std::{name}::block{ci}",
                "source": name,
                "doc_type": "standard",
                "tier": 1,
                "clause": None,
                "page": page_for_pos[0] if page_for_pos else None,
                "text": sub,
                "char_count": len(sub),
            })
        return chunks

    for i, m in enumerate(matches):
        clause = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        sub = full_text[start:end].strip()
        if len(sub) < MIN_CHUNK_CHARS:
            continue
        page = page_for_pos[start] if start < len(page_for_pos) else None

        if len(sub) > MAX_CHUNK_CHARS:
            for ci, ss in enumerate(_split_by_length(sub, MAX_CHUNK_CHARS)):
                chunks.append({
                    "id": f"std::{name}::{clause}_p{ci}",
                    "source": name,
                    "doc_type": "standard",
                    "tier": 1,
                    "clause": clause,
                    "page": page,
                    "text": ss,
                    "char_count": len(ss),
                })
        else:
            chunks.append({
                "id": f"std::{name}::{clause}",
                "source": name,
                "doc_type": "standard",
                "tier": 1,
                "clause": clause,
                "page": page,
                "text": sub,
                "char_count": len(sub),
            })

    return chunks


def chunk_internal(doc: dict):
    src = doc["source_file"]
    ext = doc["ext"]
    text = doc.get("text", "")
    cat = doc.get("category", "contracts")

    # 表格类:不切结构,只按长度拆
    is_table = ext in (".xlsx", ".xls")
    doc_type = "rate_table" if is_table else ("contract" if cat == "contracts" else cat[:-1])

    chunks = []

    if is_table:
        for ci, sub in enumerate(_split_by_length(text, MAX_CHUNK_CHARS)):
            chunks.append({
                "id": f"rate::{src}::{ci}",
                "source": src,
                "doc_type": doc_type,
                "tier": 2,
                "text": sub,
                "char_count": len(sub),
            })
        return chunks

    # 合同:按"第X条"切
    matches = list(CONTRACT_ARTICLE.finditer(text))
    if len(matches) >= 3:
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sub = text[start:end].strip()
            if len(sub) < MIN_CHUNK_CHARS:
                continue
            if len(sub) > MAX_CHUNK_CHARS:
                for ci, ss in enumerate(_split_by_length(sub, MAX_CHUNK_CHARS)):
                    chunks.append({
                        "id": f"contract::{src}::a{i + 1}_p{ci}",
                        "source": src,
                        "doc_type": doc_type,
                        "tier": 2,
                        "article": i + 1,
                        "text": ss,
                        "char_count": len(ss),
                    })
            else:
                chunks.append({
                    "id": f"contract::{src}::a{i + 1}",
                    "source": src,
                    "doc_type": doc_type,
                    "tier": 2,
                    "article": i + 1,
                    "text": sub,
                    "char_count": len(sub),
                })
    else:
        # 没条款标记,按长度切
        for ci, sub in enumerate(_split_by_length(text, MAX_CHUNK_CHARS)):
            chunks.append({
                "id": f"contract::{src}::{ci}",
                "source": src,
                "doc_type": doc_type,
                "tier": 2,
                "text": sub,
                "char_count": len(sub),
            })

    return chunks


def chunk_report(rec: dict):
    if rec.get("char_count", 0) < MIN_CHUNK_CHARS:
        return []
    return [{
        "id": f"report::{rec['source_file']}::p{rec['page_in_pdf']}",
        "source": rec["source_file"],
        "doc_type": "report",
        "tier": 2,
        "page": rec["page_in_pdf"],
        "text": rec["ocr_text"],
        "char_count": rec["char_count"],
    }]


def main():
    all_chunks = []
    seen_ids: set[str] = set()

    def unique_id(base: str) -> str:
        if base not in seen_ids:
            seen_ids.add(base)
            return base
        n = 1
        while f"{base}#{n}" in seen_ids:
            n += 1
        new_id = f"{base}#{n}"
        seen_ids.add(new_id)
        return new_id

    def add_chunks(chunks):
        for c in chunks:
            c["id"] = unique_id(c["id"])
            all_chunks.append(c)

    if STANDARDS_RAW.exists():
        print(f"[*] {STANDARDS_RAW.name}")
        with STANDARDS_RAW.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                doc = json.loads(line)
                cks = chunk_standard(doc)
                print(f"    {doc['name'][:60]}: {len(cks)} chunks")
                add_chunks(cks)
    else:
        print(f"[!] {STANDARDS_RAW} 还没生成,跳过")

    if INTERNAL_RAW.exists():
        print(f"\n[*] {INTERNAL_RAW.name}")
        n_per_src = 0
        with INTERNAL_RAW.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                doc = json.loads(line)
                cks = chunk_internal(doc)
                n_per_src += len(cks)
                add_chunks(cks)
        print(f"    合计 {n_per_src} chunks")
    else:
        print(f"[!] {INTERNAL_RAW} 还没生成,跳过")

    if REPORTS_RAW.exists():
        print(f"\n[*] {REPORTS_RAW.name}")
        n_report = 0
        with REPORTS_RAW.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                cks = chunk_report(rec)
                n_report += len(cks)
                add_chunks(cks)
        print(f"    合计 {n_report} chunks")
    else:
        print(f"[!] {REPORTS_RAW} 还没生成,跳过")

    if not all_chunks:
        print("\n[X] 没有任何 chunks 可写")
        sys.exit(1)

    CHUNKS_OUT.parent.mkdir(exist_ok=True, parents=True)
    with CHUNKS_OUT.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # 统计
    by_type, by_source = {}, {}
    total_chars = 0
    for c in all_chunks:
        by_type[c["doc_type"]] = by_type.get(c["doc_type"], 0) + 1
        by_source[c["source"]] = by_source.get(c["source"], 0) + 1
        total_chars += c["char_count"]

    print(f"\n[OK] 写入 {CHUNKS_OUT}")
    print(f"     共 {len(all_chunks)} chunks / {total_chars:,} 字")
    print(f"     按类型: {by_type}")
    print(f"     来源数: {len(by_source)}")


if __name__ == "__main__":
    main()
