import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data", "knowledge")
VECTOR_DIR = os.path.join(BASE_DIR, "vector_store")

embeddings = None

def get_embeddings():
    # This is your local path that works right now
    local_path = r"C:\Users\Dennis\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
    
    # Check if the local folder actually exists on this machine
    if os.path.exists(local_path):
        model_identifier = local_path
    else:
        # This is what GitHub/Production will use
        model_identifier = "sentence-transformers/all-MiniLM-L6-v2"
        
    embeddings = HuggingFaceEmbeddings(model_name=model_identifier)
    return embeddings

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

    embeddings = get_embeddings()

    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(VECTOR_DIR)

def search_company_knowledge(company: str, query: str):
    embeddings = get_embeddings()

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