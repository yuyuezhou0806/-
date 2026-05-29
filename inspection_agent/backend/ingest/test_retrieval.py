"""测试向量库的检索质量。

跑一组工程检测相关的真实查询,看 top-K 的命中。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = ROOT / "data" / "chroma"
MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
COLLECTION = "inspection_kb"
TOP_K = 5

QUERIES = [
    "砌体加固改造工程需要做哪些检测项目",
    "回弹法检测混凝土抗压强度的取样数量要求",
    "钢筋保护层厚度检测精度",
    "建筑变形沉降观测的精度等级和频率",
    "既有建筑结构鉴定的程序和方法",
    "钢结构焊缝无损检测的依据规范",
    "饰面砖粘结强度怎么检测",
    "灌浆套筒钢筋接头平行检测",
    "上海地区抗震设防烈度规定",
    "混凝土后锚固的拉拔试验要求",
]


def main():
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"[X] 依赖缺失: {e}")
        sys.exit(1)

    if not CHROMA_DIR.exists():
        print(f"[X] Chroma 目录不存在: {CHROMA_DIR}")
        print("    先跑 embed_and_store.py")
        sys.exit(1)

    print(f"[*] 加载 {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"[*] 打开 Chroma: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    coll = client.get_collection(COLLECTION)
    print(f"    collection={COLLECTION}, docs={coll.count()}\n")

    for q in QUERIES:
        print("=" * 80)
        print(f"Q: {q}")
        emb = model.encode(
            [q], normalize_embeddings=True, show_progress_bar=False
        ).tolist()
        result = coll.query(
            query_embeddings=emb,
            n_results=TOP_K,
        )
        ids = result["ids"][0]
        docs = result["documents"][0]
        dists = result["distances"][0]
        metas = result["metadatas"][0]

        for rank, (idx, doc, dist, md) in enumerate(zip(ids, docs, dists, metas), 1):
            doc_type = md.get("doc_type", "?")
            source = md.get("source", "?")
            clause = md.get("clause", "")
            similarity = 1 - dist  # cosine distance → similarity
            preview = doc.replace("\n", " ")[:150]
            tag = f"[{doc_type}]"
            if clause:
                tag += f" {clause}"
            print(f"  {rank}. sim={similarity:.3f} {tag} ← {source[:50]}")
            print(f"     {preview}...")
        print()


if __name__ == "__main__":
    main()
