import os
import time
import json
import glob
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
import streamlit as st

# Define constants
SETTINGS_FILE = "bank_settings.json"
DATA_FOLDER = "data"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def reset_settings():
    if os.path.exists(SETTINGS_FILE):
        os.remove(SETTINGS_FILE)

def ingest_documents():
    # Load environment variables and settings from Streamlit secrets
    PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
    # Ensure index name meets Pinecone's naming requirements:
    PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"].lower().replace("_", "-")
    COHERE_API_KEY = st.secrets["COHERE_API_KEY"]
    
    # Initialize Pinecone using the new API
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing_indexes = pc.list_indexes().names()  # Get a list of existing index names
    if PINECONE_INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=1024,  # Cohere's embed-english-v3.0 returns 1024-dimensional vectors
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        while not pc.describe_index(PINECONE_INDEX_NAME)["status"]["ready"]:
            time.sleep(1)
    
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Initialize Cohere embeddings
    embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)
    
    # Create the Pinecone vector store
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    
    # Load all PDF documents from the data folder
    pdf_files = glob.glob(os.path.join(DATA_FOLDER, "*.pdf"))
    documents = []
    for file in pdf_files:
        loader = PyPDFLoader(file)
        documents.extend(loader.load())
    
    if not documents:
        st.error("No valid PDF documents found in the data folder.")
        return

    # Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    
    # Set your custom vector ID manually (here we use "zenith")
    custom_id = "zenith"
    # Use the same custom ID for every chunk so that upsert updates the existing entry
    ids = [custom_id for _ in chunks]
    
    # Upsert the document chunks into Pinecone
    vector_store.add_documents(documents=chunks, ids=ids)
    print("Ingestion complete: vectors upserted with your custom ID.")

# Example usage in Streamlit:
st.title("Avnicore AI Setup")

# Load any previously saved settings
settings = load_settings()

# Input fields with pre-populated values if available
bank_name = st.text_input("Bank Name", value=settings.get("bank_name", ""), placeholder="Enter the bank name")
url = st.text_input("URL", value=settings.get("url", ""), placeholder="Enter the bank's URL")
prompt = st.text_area("Instruction", value=settings.get("prompt", ""), placeholder="Enter the detailed instructions for the AI")

# File uploader for the document
uploaded_file = st.file_uploader("Upload Documents for knowledge base", type=["pdf", "docx", "txt"])

if st.button("Save Settings"):
    # Update settings dictionary with the current input values
    settings["bank_name"] = bank_name
    settings["url"] = url
    settings["prompt"] = prompt

    if uploaded_file is not None:
        # Create a file path within the data folder and save the uploaded file
        file_path = os.path.join(DATA_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        settings["document"] = file_path
    else:
        settings["document"] = None
    
    ingest_documents()
    save_settings(settings)
    st.success("Settings saved and file stored in the data folder!")

if st.button("Reset Settings"):
    reset_settings()
    st.success("Settings have been reset!")
