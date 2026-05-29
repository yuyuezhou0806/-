# 检测行业智能助手 Agent

工程检测领域的 RAG + Agent。输入项目情况 → 输出检测项清单 / 适用标准 / 预估工作量 / 历史缺陷风险。

## 路线图

- **Week 1** 数据准备:规范文档 → 切段 → 向量库
- **Week 2** Agent 搭建:LangGraph + 3 个 tools + badcase eval
- **Week 3** 前端 + Vercel 上线
- **Bonus** 包装成 MCP server

## 现在做什么

1. **准备规范 PDF** —— 详见 [docs/数据准备清单.md](docs/数据准备清单.md)
   - 把所有 PDF 放到 `data/standards/`
2. **装依赖**(进入 `.venv` 后):
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **跑 PDF 提取**:
   ```bash
   python backend/ingest/load_pdfs.py
   ```
   生成 `data/raw_text.jsonl`,每行 = 一份规范的全文
4. 后续 chunk / embed / agent 等我给你下一步指令再做

## 数据源

- 国标 GB / 行标 JGJ / 上海地标 DGJ 工程检测相关规范(自己搜)
- 公司内部合同样本 / 报告模板 / 费率表(从公司拿)
- IDI 缺陷库 599 条(已在 `../idi_defects/data/defects.json`)

## 技术栈

| 层 | 选型 |
|---|------|
| LLM | Claude Sonnet 4.6 API |
| Agent | LangGraph |
| Vector DB | Chroma (dev) → Supabase pgvector (prod) |
| Embedding | bge-large-zh |
| Backend | FastAPI |
| Frontend | Next.js 16 + Vercel AI SDK |
| 部署 | Vercel + Supabase |

## 目录

```
inspection_agent/
├── README.md
├── .env.example
├── .gitignore
├── data/
│   ├── standards/         你的 PDF 放这里
│   ├── raw_text.jsonl     load_pdfs.py 产物
│   └── chunks.jsonl       chunk.py 产物(Week 1 后期)
├── docs/
│   └── 数据准备清单.md
└── backend/
    ├── requirements.txt
    ├── ingest/            数据预处理脚本
    ├── tools/             Agent 的工具(Week 2)
    ├── agent.py           LangGraph 主 agent(Week 2)
    └── main.py            FastAPI(Week 2)
```
