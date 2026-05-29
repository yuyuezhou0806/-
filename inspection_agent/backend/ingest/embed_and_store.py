"""把 chunks.jsonl 全部 embed 后入 Chroma 向量库

模型: BAAI/bge-base-zh-v1.5 (~400MB,中文检索质量足够;想用 large 改 EMBEDDING_MODEL)
向量库: Chroma 持久化在 data/chroma/
collection: inspection_kb

国内首次下载模型走 hf-mirror.com
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 国内下模型走 hf-mirror
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

ROOT = Path(__file__).resolve().parent.parent.parent
CHUNKS = ROOT / "data" / "chunks.jsonl"
CHROMA_DIR = ROOT / "data" / "chroma"

MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
COLLECTION = "inspection_kb"
BATCH_SIZE = 32


def main():
    try:
        from sentence_transformers import SentenceTransformer
        import chromadb
        from tqdm import tqdm
    except ImportError as e:
        print(f"[X] 依赖未装: {e}")
        print("    跑: pip install sentence-transformers chromadb tqdm")
        sys.exit(1)

    if not CHUNKS.exists():
        print(f"[X] {CHUNKS} 不存在,先跑 chunk.py")
        sys.exit(1)

    print(f"[*] 加载 embedding 模型: {MODEL_NAME}")
    print(f"    (首次下载 ~400MB,通过 hf-mirror.com)")
    model = SentenceTransformer(MODEL_NAME)
    print(f"    模型维度: {model.get_sentence_embedding_dimension()}")

    print(f"\n[*] 初始化 Chroma: {CHROMA_DIR}")
    CHROMA_DIR.mkdir(exist_ok=True, parents=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        client.delete_collection(COLLECTION)
        print(f"    删除旧 collection: {COLLECTION}")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    # 读 chunks
    chunks = []
    with CHUNKS.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    print(f"\n[*] 共 {len(chunks)} chunks 待 embed")

    # 分批
    n_done = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        docs = [c["text"] for c in batch]
        ids = [c["id"] for c in batch]
        metas = []
        for c in batch:
            md = {}
            for k, v in c.items():
                if k == "text":
                    continue
                # Chroma metadata 不支持 None
                if v is None:
                    md[k] = ""
                elif isinstance(v, (str, int, float, bool)):
                    md[k] = v
                else:
                    md[k] = str(v)
            metas.append(md)

        embeds = model.encode(
            docs,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        collection.add(
            ids=ids,
            documents=docs,
            embeddings=embeds,
            metadatas=metas,
        )
        n_done += len(batch)
        pct = n_done / len(chunks) * 100
        print(f"  进度: {n_done}/{len(chunks)} ({pct:.1f}%)", flush=True)

    print(f"\n[OK] 向量库写入完成: {CHROMA_DIR}")
    print(f"     collection={COLLECTION}, docs={collection.count()}")


if __name__ == "__main__":
    main()
