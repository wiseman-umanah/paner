from pathlib import Path
import uuid
from typing import List
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from .ai import load_prompt, answer_question


chroma_client = chromadb.Client()
vector_store = chroma_client.create_collection(name="paner_collection")

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=100
    )
model = SentenceTransformer("all-MiniLM-L6-v2")

DOCUMENT_CACHE: List[Document] = []
CURRENT_DOCUMENT_NAME: str | None = None


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
    data  = loader.load()

    chunks = text_splitter.split_documents(data)
    return chunks


def _format_chunk(text: str, metadata: dict | None) -> str:
    """
    Format chunk text with metadata for better answers.
    """
    metadata = metadata or {}
    source = metadata.get("source")
    source_name = Path(source).name if source else "Document"
    page = metadata.get("page")
    page_label = f" | Page: {page + 1}" if isinstance(page, int) else ""
    return f"Source: {source_name}{page_label}\n{text}"


def _remember_document(data: list[Document], source_path: str) -> None:
    """
    Keep a lightweight cache of the most recent document for smarter fallbacks.
    """
    global DOCUMENT_CACHE, CURRENT_DOCUMENT_NAME
    DOCUMENT_CACHE = data
    CURRENT_DOCUMENT_NAME = Path(source_path).name


def add_to_vector(data: list[Document]) -> bool:
    """
    Add pdf vector representation to vector database
    """
    try:
        texts = [doc.page_content for doc in data]
        embeddings = model.encode(texts).tolist()
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]

        metadatas = []
        for doc in data:
            meta = doc.metadata.copy()
            meta.setdefault("source", doc.metadata.get("source"))
            metadatas.append(meta)

        vector_store.add(
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
        )
        return True
    except Exception as e:
        print(e)
        return False


def get_from_vector(query: str, n_results: int = 8) -> list[str]:
    """
    Retrieve data from vector database
    """
    encoded_query = model.encode([query]).tolist()

    results = vector_store.query(
        query_embeddings=encoded_query,
        n_results=n_results
    )

    documents = results.get("documents")
    metadatas = results.get("metadatas")
    if not documents or not documents[0]:
        return []

    formatted = []
    for text, metadata in zip(documents[0], (metadatas or [[]])[0]):
        formatted.append(_format_chunk(text, metadata))
    return formatted


def get_document_overview(max_chunks: int = 8) -> list[str]:
    """
    Provide a general overview of the cached document when retrieval fails.
    """
    if not DOCUMENT_CACHE:
        return []

    if len(DOCUMENT_CACHE) <= max_chunks:
        docs = DOCUMENT_CACHE
    else:
        step = max(1, len(DOCUMENT_CACHE) // max_chunks)
        docs = DOCUMENT_CACHE[::step][:max_chunks]

    overview = []
    for doc in docs:
        overview.append(_format_chunk(doc.page_content, doc.metadata))
    return overview


def handle_prompt(text: str):
    text = normalize_input(text)
    if is_pdf(text):
        data = read_pdf(text)
        if add_to_vector(data):
            _remember_document(data, text)
            name = CURRENT_DOCUMENT_NAME or "document"
            return f"I have analyzed your document: {name}. Ask me anything about it."
        else:
            return "Failed to process the document"
    else:
        chunks = get_from_vector(text)
        if not chunks:
            chunks = get_document_overview()
            if not chunks:
                return "I couldn't find relevant information in the document."
        context = '\n\n'.join(chunks)
        prompt = load_prompt(context=context, question=text)
        feedback = answer_question(prompt=prompt)
        return feedback
