from pydantic import BaseModel
from langchain.tools import tool

class BLOCKSchema(BaseModel):
    account_number: str


@tool(args_schema=BLOCKSchema)
def block_account_tool(account_number):
    """
    Tool to block a user's account.
    Args:
        account_number: The user's account number
    Returns:
        A message confirming that the account has been blocked
    """
    print("INSIDE BLOCK ACCOUNT NODE")
    return f"Account {account_number} has been blocked."

@tool(args_schema=BLOCKSchema)
def block_card_tool(account_number):
    """
    Tool to block a user's card.
    Args:
        account_number: The user's account number
    Returns:
        A message confirming that the card has been blocked
    """
    print("INSIDE BLOCK CARD NODE")
    return f"Card for account {account_number} has been blocked."
