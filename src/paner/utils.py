from __future__ import annotations

from pathlib import Path
import uuid
from typing import Dict, List, Optional, Tuple

from rich.prompt import Confirm

try:
    from duckduckgo_search import DDGS
except ImportError:  # pragma: no cover - optional dependency
    DDGS = None

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

from .ai import load_prompt, answer_question


_chroma_client: chromadb.Client | None = None
_vector_store = None
_embedding_model: SentenceTransformer | None = None

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=100,
)

DOCUMENT_CACHES: Dict[str, List[Document]] = {}
DOCUMENT_REGISTRY: Dict[str, Dict[str, str]] = {}
CURRENT_DOCUMENT_ID: Optional[str] = None


def get_vector_store():
    """
    Lazily initialize and return the Chroma collection.
    """
    global _chroma_client, _vector_store
    if _vector_store is None:
        _chroma_client = chromadb.Client()
        _vector_store = _chroma_client.create_collection(name="paner_collection")
    return _vector_store


def get_embedding_model() -> SentenceTransformer:
    """
    Lazily load the sentence transformer to avoid slow startup.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def normalize_input(text: str) -> str:
    """
    Trim whitespace and surrounding quotes from user input.
    """
    stripped = text.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1].strip()
    return stripped


def is_pdf(text: str) -> bool:
    """
    Check if a text stream is pdf
    """
    p = Path(text.strip())
    return p.exists() and p.suffix.lower() == '.pdf'


def read_pdf(path) -> list[Document]:
    """
    Read the contents of the pdf, returned as chunks
    """
    loader = PyMuPDFLoader(path)
    data = loader.load()

    chunks = text_splitter.split_documents(data)
    return chunks


def _set_current_document(doc_id: Optional[str]) -> None:
    """
    Update the currently focused document.
    """
    global CURRENT_DOCUMENT_ID
    CURRENT_DOCUMENT_ID = doc_id if doc_id in DOCUMENT_REGISTRY else None


def get_active_document_name() -> Optional[str]:
    """
    Returns the name of the currently focused document.
    """
    if CURRENT_DOCUMENT_ID is None:
        return None
    info = DOCUMENT_REGISTRY.get(CURRENT_DOCUMENT_ID)
    if not info:
        return None
    return info["name"]


def list_documents() -> List[Dict[str, str | int | bool]]:
    """
    List all loaded documents with their metadata for CLI display.
    """
    docs = []
    for index, (doc_id, info) in enumerate(DOCUMENT_REGISTRY.items(), start=1):
        docs.append(
            {
                "index": index,
                "id": doc_id,
                "name": info["name"],
                "path": info["path"],
                "is_active": doc_id == CURRENT_DOCUMENT_ID,
            }
        )
    return docs


def select_document(identifier: str) -> Tuple[bool, str]:
    """
    Switch focus to a specific document or all documents.
    """
    if not DOCUMENT_REGISTRY:
        return False, "No PDFs loaded yet. Drop a PDF path first."

    ident = identifier.strip()
    if not ident or ident.lower() == "all":
        _set_current_document(None)
        return True, "Queries will consider all loaded documents."

    docs = list(DOCUMENT_REGISTRY.items())
    if ident.isdigit():
        idx = int(ident) - 1
        if 0 <= idx < len(docs):
            doc_id = docs[idx][0]
            _set_current_document(doc_id)
            name = DOCUMENT_REGISTRY[doc_id]["name"]
            return True, f"Now focusing on '{name}'."
        return False, f"Document number {ident} is out of range."

    ident_lower = ident.lower()
    for doc_id, info in docs:
        if info["name"].lower() == ident_lower:
            _set_current_document(doc_id)
            return True, f"Now focusing on '{info['name']}'."

    return False, f"Could not find a document named '{identifier}'."


def _remember_document(doc_id: str, doc_name: str, data: List[Document], source_path: str) -> None:
    """
    Store document metadata/caches using an existing document id.
    """
    DOCUMENT_CACHES[doc_id] = data
    DOCUMENT_REGISTRY[doc_id] = {"name": doc_name, "path": str(source_path)}
    _set_current_document(doc_id)


def _format_chunk(text: str, metadata: Optional[dict]) -> str:
    """
    Format chunk text with metadata for better answers.
    """
    metadata = metadata or {}
    source = metadata.get("source")
    source_name = Path(source).name if source else "Document"
    page = metadata.get("page")
    page_label = f" | Page: {page + 1}" if isinstance(page, int) else ""
    return f"Source: {source_name}{page_label}\n{text}"


def add_to_vector(data: list[Document], doc_id: str) -> bool:
    """
    Add pdf vector representation to vector database
    """
    try:
        model = get_embedding_model()
        texts = [doc.page_content for doc in data]
        embeddings = model.encode(texts).tolist()
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]

        metadatas = []
        for doc in data:
            meta = doc.metadata.copy()
            meta.setdefault("source", doc.metadata.get("source"))
            meta["doc_id"] = doc_id
            metadatas.append(meta)

        vector_store = get_vector_store()
        vector_store.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        return True
    except Exception as e:
        print(e)
        return False


def _query_vector_store(query_embedding, n_results: int, doc_id: Optional[str]):
    vector_store = get_vector_store()
    kwargs = {
        "query_embeddings": query_embedding,
        "n_results": n_results,
    }
    if doc_id:
        kwargs["where"] = {"doc_id": doc_id}
    return vector_store.query(**kwargs)


def get_from_vector(query: str, n_results: int = 8, doc_id: Optional[str] = None) -> list[str]:
    """
    Retrieve data from vector database
    """
    model = get_embedding_model()
    encoded_query = model.encode([query]).tolist()

    results = _query_vector_store(encoded_query, n_results, doc_id)

    documents = results.get("documents")
    metadatas = results.get("metadatas")
    if not documents or not documents[0]:
        return []

    formatted = []
    for text, metadata in zip(documents[0], (metadatas or [[]])[0]):
        formatted.append(_format_chunk(text, metadata))
    return formatted


def _sample_chunks(documents: List[Document], limit: int) -> List[str]:
    if not documents or limit <= 0:
        return []
    if len(documents) <= limit:
        selection = documents
    else:
        step = max(1, len(documents) // limit)
        selection = documents[::step][:limit]
    return [_format_chunk(doc.page_content, doc.metadata) for doc in selection]


def get_document_overview(doc_id: Optional[str] = None, max_chunks: int = 8) -> list[str]:
    """
    Provide a general overview of cached documents when retrieval fails.
    """
    if doc_id:
        return _sample_chunks(DOCUMENT_CACHES.get(doc_id, []), max_chunks)

    if not DOCUMENT_CACHES:
        return []

    chunks: List[str] = []
    share = max(1, max_chunks // len(DOCUMENT_CACHES))
    for cache in DOCUMENT_CACHES.values():
        chunks.extend(_sample_chunks(cache, share))
    return chunks[:max_chunks]


def _answer_with_context(chunks: List[str], question: str) -> str:
    context = '\n\n'.join(chunks)
    prompt = load_prompt(context=context, question=question)
    return answer_question(prompt=prompt)


def _is_web_search_available() -> bool:
    return DDGS is not None


def search_web(query: str, max_results: int = 5) -> List[str]:
    """
    Run a lightweight DuckDuckGo search and return formatted snippets.
    """
    if not _is_web_search_available():
        return []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:  # pragma: no cover - network errors
        print(f"Web search failed: {exc}")
        return []

    chunks = []
    for idx, item in enumerate(results, start=1):
        title = item.get("title") or "Result"
        body = item.get("body") or item.get("snippet") or ""
        href = item.get("href") or item.get("url") or ""
        chunks.append(f"Web Result {idx}: {title}\n{body}\nLink: {href}")
    return chunks


def _try_web_search(question: str) -> str:
    """
    Offer to search the web and answer using those snippets.
    """
    if not _is_web_search_available():
        return (
            "I couldn't find this in your documents and web search isn't available. "
            "Install 'duckduckgo-search' to enable it."
        )

    should_search = Confirm.ask(
        "[bold yellow]I couldn't find this in your documents. Search the web?[/bold yellow]",
        default=False,
    )
    if not should_search:
        return "I couldn't find relevant information in the document."

    snippets = search_web(question)
    if not snippets:
        return "Web search didn't return useful information."

    answer = _answer_with_context(snippets, question)
    return f"Here's what I found online:\n{answer}"


def handle_prompt(text: str):
    text = normalize_input(text)
    if is_pdf(text):
        data = read_pdf(text)
        doc_id = str(uuid.uuid4())
        doc_name = Path(text).name
        if add_to_vector(data, doc_id):
            _remember_document(doc_id, doc_name, data, text)
            return (
                f"I have analyzed '{doc_name}'. "
                "Use `list` to view all PDFs or `use <name|number|all>` to change focus."
            )
        else:
            return "Failed to process the document"
    else:
        chunks = get_from_vector(text, doc_id=CURRENT_DOCUMENT_ID)
        if not chunks:
            chunks = get_document_overview(CURRENT_DOCUMENT_ID)
            if not chunks:
                return _try_web_search(text)
        feedback = _answer_with_context(chunks, text)
        return feedback
