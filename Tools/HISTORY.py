from pydantic import BaseModel
from langchain.tools import tool
import requests

class TransactionHistorySchema(BaseModel):
    account_number: str

@tool(args_schema=TransactionHistorySchema)
def retrieve_transaction_history_tool(account_number):
    """
    Tool to Retrieve a user's transaction history from the bank's database.
    Args:
        account_number: The user's account number
    Returns:
        The user's transaction history
    """
    print("INSIDE TRANSACTION HISTORY NODE")
    url = f"https://avnipay.onrender.com/api/v1/auth/transaction-history/{account_number}"
    response = requests.get(url)
    return response.json()