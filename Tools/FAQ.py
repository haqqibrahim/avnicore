import streamlit as st
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_cohere import CohereEmbeddings
from langchain_pinecone import PineconeVectorStore
from pydantic import BaseModel
from langchain.tools import tool

def get_vector_store() -> PineconeVectorStore:
    """
    Initializes the Pinecone vector store using environment variables.
    Assumes that ingestion has already been done.
    """
    load_dotenv()
    PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
    # Ensure the index name complies with Pinecone naming rules.
    PINECONE_INDEX_NAME = st.secrets["PINECONE_INDEX_NAME"].lower().replace("_", "-")
    COHERE_API_KEY = st.secrets["COHERE_API_KEY"]
    
    # Initialize the Pinecone client using the new API
    pc = Pinecone(api_key=PINECONE_API_KEY)
    # Retrieve the index; this assumes the index already exists
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Initialize the Cohere embeddings model (embed-english-v3.0 outputs 1024-d vectors)
    embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=COHERE_API_KEY)
    
    # Create and return the Pinecone vector store
    return PineconeVectorStore(index=index, embedding=embeddings)

# Define a Pydantic schema for the retrieval tool
class RagToolSchema(BaseModel):
    question: str

@tool(args_schema=RagToolSchema)
def retriever_tool(question: str) -> str:
    """Consult the banks policies and FAQ tto answer User Questions or Enqueires related to to the bank, 
    account opening, managing of account, IT issues etc.
  """
    print("INSIDE RETRIEVER NODE")
    vector_store = get_vector_store()
    # Create a retriever with desired search parameters:
    retriever = vector_store.as_retriever(search_kwargs={"k": 2, "score_threshold": 0.5})
    results = retriever.invoke(question)
    # Concatenate the content of the retrieved document chunks
    return "\n\n".join(doc.page_content for doc in results)
