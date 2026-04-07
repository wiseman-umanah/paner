from pathlib import Path
import uuid
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb



chroma_client = chromadb.Client()
vector_store = chroma_client.create_collection(name="paner_collection")

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=10
    )
model = SentenceTransformer("all-MiniLM-L6-v2")


def is_pdf(text: str) -> bool:
    """
    Check if a text stream is pdf
    """
    p = Path(text.strip())
    return p.exists() and p.suffix.lower() == '.pdf'


def read_pdf(path) -> list[Document]:
    loader = PyMuPDFLoader(path)
    data  = loader.load()

    chunks = text_splitter.split_documents(data)
    return chunks


def add_to_vector(data: list[Document]) -> bool:
    try:
        texts = [doc.page_content for doc in data]
        embeddings = model.encode(texts)
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]

        vector_store.add(
                documents=texts,
                embeddings=embeddings,
                ids=ids
        )
        return True
    except Exception as e:
        print(e)
        return False

def get_from_vector():
    pass

def handle_prompt(text: str):
    # check if pdf, save to vector db
    if is_pdf(text):
        data = read_pdf(text)
        if add_to_vector(data)
            return "I have analyzed your document"
        else:
            return "Failed to process the document"

    # else, with vector store and ai answer user question
    # respond with i dont know, should I search the web for the information?for data  that is not in vector store.
    pass
