import os
import time
import json
from typing import List
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pydantic import BaseModel
from langchain.tools import tool

# -----------------------------
# Ingestion and Upsert Section
# -----------------------------
# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")

with open('bank_settings.json', 'r') as f:
    settings = json.load(f)

# Initialize Pinecone using the new API.
pc = Pinecone(api_key=PINECONE_API_KEY)
existing_indexes = pc.list_indexes().names()  # Get list of index names
if PINECONE_INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1024,  # Cohere's embed-english-v3.0 output dimension is 1024
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    while not pc.describe_index(PINECONE_INDEX_NAME)["status"]["ready"]:
        time.sleep(1)

index = pc.Index(PINECONE_INDEX_NAME)

# Initialize Cohere embeddings (use 'cohere_api_key' for Cohere)
embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)

# Create the Pinecone vector store
vector_store = PineconeVectorStore(index=index, embedding=embeddings)

# Load documents from the "data" directory (PDF files in this example)
def load_documents(folder_path: str) -> List[Document]:
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith('.pdf'):
            print("PDF document found")
            loader = PyPDFLoader(file_path)
        elif filename.endswith('.docx'):
            print("DOCX document found")
            loader = Docx2txtLoader(file_path)
        else:
            print(f"Unsupported file type: {filename}")
            continue
        documents.extend(loader.load())
    return documents

folder_path = "data"
documents = load_documents(folder_path)
print(f"Loaded {len(documents)} documents from the folder.")

# Split documents into manageable chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.split_documents(documents)

# -----------------------------
# Setting Custom Vector ID
# -----------------------------
# Set a custom vector ID using a value from your settings (for example, the bank name)
custom_id = settings.get("bank_name")
# Use the same custom ID for every chunk so that upsert will update the existing entry.
ids = [custom_id for _ in chunks]

# Upsert the document chunks into Pinecone using your specified ID.
vector_store.add_documents(documents=chunks, ids=ids)
print("Ingestion complete: vectors upserted with your custom ID.")

# -----------------------------
# Retrieval RAG Tool Section
# -----------------------------
class RagToolSchema(BaseModel):
    question: str

@tool(args_schema=RagToolSchema)
def retriever_tool(question: str) -> str:
    """Consult the banks policies and FAQ tto answer User Questions or Enqueires related to to the bank, 
    account opening, managing of account, IT issues etc"""
    print("Inside retriever tool")
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 2, "score_threshold": 0.5}
    )
    results = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in results)

