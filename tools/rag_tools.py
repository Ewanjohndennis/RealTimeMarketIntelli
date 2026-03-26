import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data", "knowledge")
VECTOR_DIR = os.path.join(BASE_DIR, "vector_store")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def build_vector_store():

    

    documents = []

    for file in os.listdir(DATA_DIR):

        if file.endswith(".txt"):

            file_path = os.path.join(DATA_DIR, file)

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

            documents.append(Document(page_content=text))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    db = FAISS.from_documents(chunks, embeddings)

    db.save_local(VECTOR_DIR)


def search_company_knowledge(company: str, query: str):

    db = FAISS.load_local(
        VECTOR_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )

    docs = db.similarity_search(
        f"{company} {query}",
        k=4
    )

    return "\n\n".join([d.page_content for d in docs])