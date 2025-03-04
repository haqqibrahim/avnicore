import sys
import os
import json
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
from langchain.tools import tool
import streamlit as st

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

load_dotenv()
# Load the environment variables    
COHERE_API_KEY = st.secrets["COHERE_API_KEY"]

with open('bank_settings.json', 'r') as f:
    settings = json.load(f)

WEBSITE = settings.get("url")

persist_directory = "./chroma_db_test1"

if not os.path.exists(persist_directory):
    print(f"Folder does not exist: {persist_directory}. Starting ingestion process.")

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

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    splits = text_splitter.split_documents(documents)
    print(f"Split the documents into {len(splits)} chunks.")

    embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)

    collection_name = "my_collection"
    vectorstore = Chroma.from_documents(
        collection_name=collection_name,
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    print("Vector store created and persisted to './chroma_db_test1'")
else:
    print(f"Folder exists: {persist_directory}. Skipping ingestion process.")
    # Optionally, load the existing vectorstore
    embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)
    vectorstore = Chroma(
        collection_name="my_collection",
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

class RagToolSchema(BaseModel):
    question: str

@tool(args_schema=RagToolSchema)
def retriever_tool(question):
    """Consult the bank's policies and FAQ to answer user questions or inquiries related to account opening,
       managing accounts, IT issues, etc.
    """
    print("INSIDE RETRIEVER NODE")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    retriever_results = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in retriever_results)
