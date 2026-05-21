"""IDI 缺陷清单检索工具

支持:
  - 多关键词 AND 模糊搜索(默认在全部文本字段)
  - 按风险期限/大类/子分类筛选
  - 按规范号匹配(如 GB50345、JGJ/T 470)
  - 列类别清单、按类别统计
  - 命中结果导出 JSON

示例:
  python search_defects.py 钢筋 锈蚀
  python search_defects.py --period 十年期
  python search_defects.py --major 防水工程
  python search_defects.py --code GB50345
  python search_defects.py --stats
  python search_defects.py 焊缝 --export hits.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

DATA_PATH = Path(__file__).parent / "data" / "defects.json"


def load_defects() -> list[dict]:
    if not DATA_PATH.exists():
        sys.exit(
            f"[!] 未找到 {DATA_PATH},请先运行: python extract_defects.py"
        )
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


# ---------- 过滤 ----------

SEARCH_FIELDS = ("problem", "standard", "suggestion", "description", "category_minor")


def normalize_code(code: str) -> str:
    """把规范号规范化用于匹配:去除空格、'/'、连字符差异等"""
    return re.sub(r"[\s\-/]", "", code).upper()


def match_keywords(d: dict, keywords: Iterable[str]) -> bool:
    """所有关键词都要在 SEARCH_FIELDS 任一字段中出现(AND)"""
    blob = " ".join(d.get(f, "") for f in SEARCH_FIELDS)
    return all(kw in blob for kw in keywords)


def match_code(d: dict, code: str) -> bool:
    if not code:
        return True
    code_norm = normalize_code(code)
    blob = " ".join(d.get(f, "") for f in ("standard", "suggestion", "description"))
    return code_norm in normalize_code(blob)


def filter_defects(
    defects: list[dict],
    keywords: list[str] | None = None,
    period: str | None = None,
    major: str | None = None,
    minor: str | None = None,
    code: str | None = None,
) -> list[dict]:
    out = defects
    if period:
        out = [d for d in out if period in d["category_period"]]
    if major:
        out = [d for d in out if major in d["category_major"]]
    if minor:
        out = [d for d in out if minor in d["category_minor"]]
    if keywords:
        out = [d for d in out if match_keywords(d, keywords)]
    if code:
        out = [d for d in out if match_code(d, code)]
    return out


# ---------- 输出 ----------

def text_width(s: str) -> int:
    """简易 East Asian Width:中日韩字符按 2 计算"""
    w = 0
    for ch in s:
        w += 2 if "一" <= ch <= "鿿" or ch in "：，。、；·" else 1
    return w


def wrap_text(text: str, width: int) -> list[str]:
    """按视觉宽度软换行,保留段落分隔"""
    lines = []
    cur = ""
    cur_w = 0
    for ch in text:
        cw = 2 if "一" <= ch <= "鿿" or ch in "：，。、；·" else 1
        if cur_w + cw > width:
            lines.append(cur)
            cur = ch
            cur_w = cw
        else:
            cur += ch
            cur_w += cw
    if cur:
        lines.append(cur)
    return lines


def print_defect(d: dict, idx: int | None = None) -> None:
    header_prefix = f"[#{idx}] " if idx is not None else ""
    print(
        f"\n{'━' * 70}\n"
        f"{header_prefix}{d['global_id']}  "
        f"【{d['category_period']}/{d['category_major']}】  "
        f"子项: {d['category_minor']}  原序号: {d['seq']}"
    )
    if d.get("submitter"):
        print(f"  提交人/备忘: {d['submitter']}")
    print("\n  ● 问题描述")
    for line in wrap_text(d["problem"] or "(无)", 66):
        print(f"    {line}")
    if d.get("standard"):
        print("\n  ● 违反规范")
        for line in wrap_text(d["standard"], 66):
            print(f"    {line}")
    print("\n  ● 纠正与预防建议")
    for line in wrap_text(d["suggestion"] or "(无)", 66):
        print(f"    {line}")


def print_summary_list(hits: list[dict]) -> None:
    print(f"\n命中 {len(hits)} 条:")
    print(f"{'ID':<7} {'期限':<8} {'大类':<22} 问题摘要")
    print("─" * 95)
    for d in hits:
        major = d["category_major"]
        # 简单按字符截断
        major_disp = major[:10] + "…" if len(major) > 11 else major
        problem = d["problem"].replace("\n", " ")
        problem_short = problem[:40] + ("…" if len(problem) > 40 else "")
        print(f"{d['global_id']:<7} {d['category_period']:<8} {major_disp:<22} {problem_short}")


# ---------- 类别清单 / 统计 ----------

def print_categories(defects: list[dict]) -> None:
    from collections import defaultdict, Counter

    tree = defaultdict(lambda: defaultdict(list))
    for d in defects:
        tree[d["category_period"]][d["category_major"]].append(d["category_minor"])

    for period, majors in tree.items():
        print(f"\n■ {period}")
        for major, minors in majors.items():
            cnt = len(minors)
            uniq_minor = Counter(minors)
            print(f"  └─ {major}  ({cnt} 条)")
            for m, n in uniq_minor.items():
                if m != major:
                    print(f"        · {m}  ×{n}")


def print_stats(defects: list[dict]) -> None:
    from collections import Counter

    print(f"\n总条目数: {len(defects)}")
    by_period = Counter(d["category_period"] for d in defects)
    print("\n[按风险期限]")
    for k, v in by_period.most_common():
        print(f"  {k}: {v} 条")

    by_major = Counter((d["category_period"], d["category_major"]) for d in defects)
    print("\n[按大类]")
    for (p, m), v in sorted(by_major.items(), key=lambda x: (-x[1], x[0])):
        print(f"  [{p}] {m}: {v} 条")


# ---------- CLI ----------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="IDI 质量险潜在缺陷清单检索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("keywords", nargs="*", help="模糊匹配关键词(多个为 AND)")
    parser.add_argument("--period", help="按风险期限筛选(十年期/五年期/两年期/机电安装)")
    parser.add_argument("--major", help="按大类工程筛选(支持子串)")
    parser.add_argument("--minor", help="按子分项筛选(支持子串)")
    parser.add_argument("--code", help="按规范号匹配(如 GB50345、JGJ/T 470)")
    parser.add_argument("--limit", type=int, default=20, help="最多展示条目数,默认 20")
    parser.add_argument("--brief", action="store_true", help="只输出摘要列表")
    parser.add_argument("--full", action="store_true", help="展示完整字段(默认行为)")
    parser.add_argument("--list-categories", action="store_true", help="列出类别树")
    parser.add_argument("--stats", action="store_true", help="按类别统计")
    parser.add_argument("--export", help="把命中结果导出为 JSON 路径")
    args = parser.parse_args()

    defects = load_defects()

    if args.list_categories:
        print_categories(defects)
        return
    if args.stats:
        print_stats(defects)
        return

    hits = filter_defects(
        defects,
        keywords=args.keywords,
        period=args.period,
        major=args.major,
        minor=args.minor,
        code=args.code,
    )

    if not hits:
        print("(没有匹配的条目)")
        return

    if args.brief:
        print_summary_list(hits[: args.limit])
    else:
        print_summary_list(hits[: args.limit])
        print(f"\n{'=' * 70}\n展示前 {min(args.limit, len(hits))} 条详细内容\n{'=' * 70}")
        for i, d in enumerate(hits[: args.limit], 1):
            print_defect(d, idx=i)

    if len(hits) > args.limit:
        print(f"\n... 还有 {len(hits) - args.limit} 条未展示,加 --limit N 看更多")

    if args.export:
        out = Path(args.export)
        out.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n已导出命中结果: {out}")


if __name__ == "__main__":
    main()
