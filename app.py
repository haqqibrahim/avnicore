from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel

from Tools.FAQ import retriever_tool
from Tools.HISTORY import retrieve_transaction_history_tool

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# RAG Tool Endpoint
class RagToolSchema(BaseModel):
    question: str

@app.post("/faq")
def faq_tool(request: RagToolSchema):
    response = retriever_tool(request.question)
    return {"answer": response}

# Transaction History Tool Endpoint
class TransactionSchema(BaseModel):
    account_number: str

@app.post("/history")
def transaction_history(request: TransactionSchema):
    response = retrieve_transaction_history_tool(request.account_number)
    return {"answer": response}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
