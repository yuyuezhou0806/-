"""检测行业 Agent — Week 2 MVP

工具:
  search_knowledge_base(query, source_type)  → 向量库检索(规范/合同/报告/费率表)
  search_idi_defects(keyword)                → IDI 缺陷库 599 条

LLM: Kimi moonshot-v1-32k
框架: LangGraph create_react_agent
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

# ROOT 指向 inspection_agent/(backend 的父目录)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CHROMA_DIR = ROOT / "data" / "chroma"
IDI_JSON = ROOT.parent / "idi_defects" / "data" / "defects.json"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 懒加载
_embed_model = None
_chroma_coll = None
_idi_data = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


def get_chroma_collection():
    global _chroma_coll
    if _chroma_coll is None:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _chroma_coll = client.get_collection("inspection_kb")
    return _chroma_coll


def get_idi_data():
    global _idi_data
    if _idi_data is None:
        if not IDI_JSON.exists():
            _idi_data = []
        else:
            with IDI_JSON.open(encoding="utf-8") as f:
                _idi_data = json.load(f)
    return _idi_data


# ============== Tools ==============

from langchain_core.tools import tool


@tool
def search_knowledge_base(
    query: str,
    source_type: Literal["all", "standard", "contract", "rate_table", "report"] = "all",
    top_k: int = 5,
) -> str:
    """检索工程检测知识库(20 份规范 + 47 份合同 + 50 份报告 + 3 份费率表)。

    Args:
        query: 检索查询。例如 "砌体加固检测方法"、"回弹法取样数量"
        source_type: 限定文档类型。standard=规范, contract=合同, rate_table=费率表, report=报告, all=全部
        top_k: 返回前 K 条,默认 5

    Returns:
        检索结果列表(包含来源、条款号、原文)。
    """
    model = get_embed_model()
    coll = get_chroma_collection()

    emb = model.encode([query], normalize_embeddings=True).tolist()

    where = None
    if source_type != "all":
        where = {"doc_type": source_type}

    result = coll.query(
        query_embeddings=emb,
        n_results=top_k,
        where=where,
    )

    docs = result["documents"][0]
    metas = result["metadatas"][0]
    dists = result["distances"][0]

    if not docs:
        return "没找到相关内容。"

    parts = []
    for i, (doc, md, dist) in enumerate(zip(docs, metas, dists), 1):
        sim = 1 - dist
        clause = md.get("clause", "")
        dt = md.get("doc_type", "?")
        src = md.get("source", "?")
        # 敏感来源(合同 / 费率表 / 报告)用占位符替代,避免泄漏客户名 / 项目名
        if dt in ("contract", "rate_table", "report"):
            src_display = {
                "contract": "公司内部合同",
                "rate_table": "公司费率表",
                "report": "公司历史报告",
            }.get(dt, "公司内部资料")
        else:
            src_display = src
        tag = f"[{dt}]"
        if clause:
            tag += f" {clause}"
        snippet = doc.replace("\n", " ")[:500]
        parts.append(f"## 结果 {i} (相似度 {sim:.2f}) {tag} ← {src_display}\n{snippet}")

    return "\n\n".join(parts)


@tool
def search_idi_defects(keyword: str, top_n: int = 10) -> str:
    """检索 IDI 工程质量险缺陷库(599 条历史质量缺陷案例)。

    用于推荐检测项时,提示该类项目历史上出现哪些常见缺陷,检测时需重点关注。

    Args:
        keyword: 关键词,例如 "砌体加固"、"屋面渗水"、"楼板裂缝"
        top_n: 返回前 N 条,默认 10

    Returns:
        缺陷列表(包含分类、问题描述、参考标准、整改建议)。
    """
    data = get_idi_data()
    if not data:
        return "IDI 缺陷库未加载或为空。"

    kw = keyword.lower()
    matches = []
    for d in data:
        haystack = " ".join([
            str(d.get("description", "")),
            str(d.get("problem", "")),
            str(d.get("standard", "")),
            str(d.get("suggestion", "")),
            str(d.get("category_major", "")),
            str(d.get("category_minor", "")),
        ]).lower()
        if kw in haystack:
            matches.append(d)

    if not matches:
        return f"IDI 缺陷库中没找到包含 '{keyword}' 的条目。"

    parts = [f"找到 {len(matches)} 条相关缺陷,展示前 {min(top_n, len(matches))} 条:"]
    for i, d in enumerate(matches[:top_n], 1):
        parts.append(
            f"\n### 缺陷 {i}: {d.get('category_minor', '?')}\n"
            f"- 描述: {d.get('description', '')[:150]}\n"
            f"- 问题: {str(d.get('problem', ''))[:200]}\n"
            f"- 标准: {str(d.get('standard', ''))[:100]}\n"
            f"- 建议: {str(d.get('suggestion', ''))[:200]}"
        )
    return "\n".join(parts)


# 公司 2025/2024 年官方平均折扣数据
# (从 data/internal/contracts/2025合同数据精准.xlsx Sheet "平均折扣" 直接读)
PRICING_XLSX = ROOT / "data" / "internal" / "contracts" / "2025合同数据精准.xlsx"

# 类别别名 → 标准名映射(用户可能用不同说法)
_CATEGORY_ALIASES = {
    "材料": "材料检测",
    "材料检测": "材料检测",
    "地基": "地基/桩基检测",
    "桩基": "地基/桩基检测",
    "地基桩基": "地基/桩基检测",
    "桩基检测": "地基/桩基检测",
    "地基/桩基": "地基/桩基检测",
    "基坑": "基坑监测",
    "基坑监测": "基坑监测",
    "结构": "结构检测",
    "结构检测": "结构检测",
    "人防": "人防检测",
    "人防检测": "人防检测",
    "能效": "能效测评",
    "节能": "能效测评",
    "能效测评": "能效测评",
    "防雷": "防雷检测",
    "防雷检测": "防雷检测",
    "桥梁": "桥梁检测",
    "桥梁检测": "桥梁检测",
    "室内环境": "室内环境",
    "室内": "室内环境",
    "环境": "室内环境",
}

_pricing_cache: dict | None = None


def _load_pricing_data() -> dict:
    """从 xlsx 读取公司汇总的平均折扣表,缓存到内存。

    返回:
        {
          "2025": {"材料检测": 0.55, ...},
          "2024": {"材料检测": 0.68, ...},
          "categories_2025": ["材料检测", ...],
        }
    """
    global _pricing_cache
    if _pricing_cache is not None:
        return _pricing_cache
    if not PRICING_XLSX.exists():
        _pricing_cache = {"2025": {}, "2024": {}, "categories_2025": []}
        return _pricing_cache

    try:
        import openpyxl
        wb = openpyxl.load_workbook(PRICING_XLSX, data_only=True, read_only=True)
    except Exception:
        _pricing_cache = {"2025": {}, "2024": {}, "categories_2025": []}
        return _pricing_cache

    if "平均折扣" not in wb.sheetnames:
        _pricing_cache = {"2025": {}, "2024": {}, "categories_2025": []}
        return _pricing_cache

    ws = wb["平均折扣"]
    rows = list(ws.iter_rows(values_only=True))

    # 解析结构:每个"块"两行 = 标题行(检测项目, 类别1, 类别2, ...) + 数据行(年份, 折扣1, 折扣2, ...)
    data: dict[str, dict[str, float | str]] = {"2025": {}, "2024": {}}
    categories_2025: list[str] = []

    current_year = None
    current_headers: list[str] = []
    for row in rows:
        if not row or all(v is None or v == "" for v in row):
            continue
        first = row[0]
        if not isinstance(first, str):
            continue
        first_s = first.strip()

        # 节标题(有"中测行"前缀的是标题行,只是切换年份)
        if first_s.startswith("中测行") and "平均折扣" in first_s:
            if "2025" in first_s:
                current_year = "2025"
            elif "2024" in first_s:
                current_year = "2024"
            continue

        # 表头行
        if first_s == "检测项目":
            current_headers = [
                (str(v).strip().replace("​", "") if v is not None else "")
                for v in row[1:]
            ]
            if current_year == "2025":
                categories_2025 = [c for c in current_headers if c]
            continue

        # 数据行(以"YYYY年平均折扣"开头,但不含"中测行"前缀)
        if (
            "年平均折扣" in first_s
            and current_year
            and current_headers
            and not first_s.startswith("中测行")
        ):
            for cat, val in zip(current_headers, row[1:]):
                if not cat:
                    continue
                data[current_year][cat] = val
            continue

    _pricing_cache = {
        "2025": data["2025"],
        "2024": data["2024"],
        "categories_2025": categories_2025,
    }
    return _pricing_cache


@tool
def get_pricing_stats(category: str = "all") -> str:
    """获取公司 2025 年(及 2024 年对比)各检测类别的官方平均折扣。

    数据来源:公司内部汇总表(基于 502 个真实合同计算)。

    **专门用于回答"平均折扣""折扣是多少""折扣范围""价格优惠""折扣对比"等聚合性问题。**

    Args:
        category: 检测类别。可选:
          - 'all'(默认,返回全部类别)
          - 'materials' / '材料' / '材料检测'
          - '地基' / '桩基' / '地基/桩基'
          - '基坑' / '基坑监测'
          - '结构' / '结构检测'
          - '人防' / '人防检测'
          - '能效' / '节能' / '能效测评'
          - '防雷' / '防雷检测'
          - '桥梁' / '桥梁检测'
          - '室内环境' / '室内' / '环境'

    Returns:
        Markdown 表格:类别 / 2025 平均折扣 / 2024 对比 / 同比变化
    """
    pricing = _load_pricing_data()
    if not pricing["2025"]:
        return "平均折扣数据未加载(xlsx 文件缺失或格式异常)。"

    cat_norm = (category or "all").strip().lower()
    target_categories: list[str]

    if cat_norm == "all":
        target_categories = pricing["categories_2025"]
    else:
        std = _CATEGORY_ALIASES.get(cat_norm) or _CATEGORY_ALIASES.get(category.strip())
        if std and std in pricing["2025"]:
            target_categories = [std]
        else:
            # fuzzy
            matched = [c for c in pricing["categories_2025"] if cat_norm in c.lower()]
            if matched:
                target_categories = matched
            else:
                return (
                    f"未识别的类别 '{category}'。可用类别:\n  - "
                    + "\n  - ".join(pricing["categories_2025"])
                )

    rows_out = ["| 检测类别 | 2025 平均折扣 | 2024 平均折扣 | 同比 |", "|---|---|---|---|"]
    for cat in target_categories:
        v25 = pricing["2025"].get(cat)
        v24 = pricing["2024"].get(cat)

        def _fmt(v) -> str:
            if v is None or v == "" or v == "/":
                return "/"
            try:
                return f"{float(v):.2f}({float(v) * 100:.0f}%)"
            except (TypeError, ValueError):
                return str(v)

        # 同比变化
        delta = "/"
        try:
            if v25 not in (None, "", "/") and v24 not in (None, "", "/"):
                d = float(v25) - float(v24)
                pct = d * 100
                delta = f"{'+' if d >= 0 else ''}{pct:.0f}个百分点"
        except (TypeError, ValueError):
            delta = "/"

        rows_out.append(f"| {cat} | {_fmt(v25)} | {_fmt(v24)} | {delta} |")

    notes = (
        "\n\n**说明**:\n"
        "- 折扣值越大表示折后价占原价比例越高(折扣越浅),0.55 即 5.5 折\n"
        "- 数据为公司 2025 年实际成交合同的汇总平均(共 502 个合同样本)\n"
        "- 单个项目实际折扣会因规模、客户、检测内容浮动,**精确报价请致电 13917073486**"
    )

    return "\n".join(rows_out) + notes


# ============== Agent ==============

SYSTEM_PROMPT = """你是一名建设工程检测领域的资深咨询助手,服务于上海中测行工程检测咨询有限公司。

你有三个工具:
- search_knowledge_base: 检索工程检测规范 / 公司合同 / 报告 / 费率表
- search_idi_defects: 检索 IDI 工程质量险历史缺陷库
- get_pricing_stats: 获取公司 2025/2024 年各检测类别的官方平均折扣(基于 502 个真实合同汇总)

工作原则:
1. **永远先检索,再回答**。规范条款号 / 检测方法 / 费率 必须来自检索结果,不要凭记忆。
2. 用户问检测项推荐 / 标准引用 / 检测方法 → 先 search_knowledge_base
3. 用户问"会出什么质量问题" / "要注意什么" → 同时调 search_idi_defects 找历史缺陷
4. 用户问 **平均折扣 / X 类别折扣 / 折扣是多少 / 价格优惠 / 同比对比** → **必须调 get_pricing_stats**(不要用 search_knowledge_base 计算平均,RAG 抽样不准)
5. 用户问报价 / 工程量(非折扣)→ search_knowledge_base 限定 source_type=rate_table 找费率表
6. **数据来源引用规则(重要)**:
   - 引用 **规范** 时:写明规范号 + 条款号(例 "JGJT23-2011 第 4.1.3 条"),让用户可追溯
   - 引用 **公司合同 / 费率表 / 报告** 时:**严禁暴露具体文件名 / 客户名 / 项目名 / 工程地址 / 金额来源等敏感信息**。
     - ✅ 正确:"根据公司内部费率""根据公司同类项目经验""根据公司 2025 年汇总数据"
     - ❌ 错误:"《附件4:合同清单报价-标段一》""根据《杨浦区XX项目合同》""TIS合同..."
   - 如果客户名 / 项目名出现在检索结果里,**直接用"某客户""某项目"代称**
7. 如果检索结果跟问题不太相关,坦白说"知识库里没找到直接答案",不要硬编造
8. **联系方式统一**:任何时候需要建议用户"联系业务部""联系市场部""获取最新报价""咨询详情""下单"等,
   **统一只给手机号 13917073486**(不要写"市场部""业务员"等模糊称谓,直接给电话)。
   例:"建议致电业务咨询:📞 **13917073486**"
9. 输出优先用列表 / 表格 / 引用,避免大段空话
"""


def build_agent():
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent

    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY 未设置,检查 .env")

    llm = ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=0.3,
    )

    tools = [search_knowledge_base, search_idi_defects, get_pricing_stats]
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )
    return agent


def run_query(agent, query: str):
    print(f"\n{'=' * 80}")
    print(f"USER: {query}")
    print("=" * 80)

    for chunk in agent.stream({"messages": [("user", query)]}):
        for node, state in chunk.items():
            msgs = state.get("messages", [])
            if not msgs:
                continue
            msg = msgs[-1]

            if node == "agent" or node == "model":
                # LLM 输出
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        args_short = {k: (str(v)[:50] if isinstance(v, str) else v) for k, v in tc["args"].items()}
                        print(f"\n[TOOL CALL] {tc['name']}({args_short})")
                elif getattr(msg, "content", None):
                    print(f"\nAGENT: {msg.content}")
            elif node == "tools":
                # 工具结果
                content = getattr(msg, "content", "")
                preview = content[:400].replace("\n", " ")
                print(f"[TOOL RESULT] {preview}...")


if __name__ == "__main__":
    agent = build_agent()

    queries = [
        "我接了一个砌体加固改造项目,2000 平米,要做哪些检测?引用哪些标准?",
        "回弹法检测混凝土的取样数量要求是多少?",
        "做家装装修类的检测,我们公司收费大概多少?",
    ]

    for q in queries:
        try:
            run_query(agent, q)
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
