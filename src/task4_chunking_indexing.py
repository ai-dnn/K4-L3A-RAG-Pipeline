"""Task 4 — Đọc Markdown, chia chunks, embed và upsert vào ChromaDB."""

import os
import math
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests


load_dotenv()
ROOT = Path(__file__).parent.parent
STANDARDIZED_DIR = ROOT / "data" / "standardized"
CHROMA_DIR = ROOT / "chroma_db"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER") or "openrouter"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "baai/bge-m3"
EMBEDDING_DIM = 1024
COLLECTION_NAME = "rag_documents"


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Dùng chung model và chuẩn hóa vector cho cả corpus lẫn query."""
    if not texts:
        return []
    if EMBEDDING_PROVIDER == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Set OPENROUTER_API_KEY in .env")
        vectors = []
        for start in range(0, len(texts), 32):
            batch = texts[start:start + 32]
            response = requests.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": EMBEDDING_MODEL, "input": batch, "encoding_format": "float"},
                timeout=(10, 120),
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            if [item["index"] for item in data] != list(range(len(batch))):
                raise ValueError("Embedding response indices do not match the input batch")
            for item in data:
                vector = item["embedding"]
                norm = math.sqrt(sum(value * value for value in vector))
                if len(vector) != EMBEDDING_DIM or not math.isfinite(norm) or norm == 0:
                    raise ValueError("Invalid embedding vector")
                vectors.append([value / norm for value in vector])
            print(f"Embedded {len(vectors)}/{len(texts)} texts", flush=True)
        return vectors
    if EMBEDDING_PROVIDER != "sentence_transformers":
        raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")
    return _get_model().encode(
        texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True,
    ).tolist()


def get_collection():
    """Mở Chroma collection persistent dùng cosine distance."""
    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL,
                  "embedding_provider": EMBEDDING_PROVIDER},
    )
    metadata = collection.metadata or {}
    if (metadata.get("hnsw:space") != "cosine"
            or metadata.get("embedding_model") != EMBEDDING_MODEL
            or metadata.get("embedding_provider") != EMBEDDING_PROVIDER):
        raise ValueError("Collection configuration differs; use a new collection or rebuild the index")
    return collection


def load_documents() -> list[dict]:
    """Giữ title/source từ header của Task 3, chỉ chunk phần nội dung."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        relative = path.relative_to(STANDARDIZED_DIR)
        if relative.parts[0] not in {"legal", "news"}:
            continue
        text = path.read_text(encoding="utf-8").strip()
        title, source, url = path.stem.replace("_", " "), path.name, None
        header, separator, body = text.partition("\n\n---\n\n")
        if separator and "**Source:** " in header:
            for line in header.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                elif line.startswith("**Source:** "):
                    value = line.removeprefix("**Source:** ").strip()
                    if value.startswith(("https://", "http://")):
                        url = value
                    else:
                        source = value
            text = body.strip()
        if text:
            documents.append({
                "id": relative.as_posix(),
                "content": text,
                "metadata": {"source": source, "title": title,
                             "doc_type": relative.parts[0], "url": url},
            })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia văn bản với ID ổn định và giữ metadata nguồn."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [
        {"id": f"{document['id']}::chunk-{index}", "content": text,
         "metadata": {**document["metadata"], "chunk_index": index}}
        for document in documents
        for index, text in enumerate(splitter.split_text(document["content"]))
        if text.strip()
    ]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Gắn embedding đúng thứ tự, không sửa input."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding count does not match chunk count")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert theo batch; chạy lại không tạo ID trùng."""
    if not chunks:
        return
    collection = get_collection()
    for start in range(0, len(chunks), 1000):
        batch = chunks[start:start + 1000]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[{key: value if value is not None else ""
                        for key, value in chunk["metadata"].items()} for chunk in batch],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    chunks = chunk_documents(load_documents())
    if not chunks:
        raise ValueError(f"No non-empty documents in {STANDARDIZED_DIR}")
    print(f"Embedding {len(chunks)} chunks with {EMBEDDING_MODEL}", flush=True)
    index_to_vectorstore(embed_chunks(chunks))
    print(f"Indexed {len(chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
