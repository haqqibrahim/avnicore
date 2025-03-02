from pydantic import BaseModel
from langchain.tools import tool

class CardDetailsSchema(BaseModel):
    account_number: str

@tool(args_schema=CardDetailsSchema)
def retrieve_card_details_tool(account_number):
    """
    Tool to retrieve a user's ATM card details from the bank's database.
    Args:
        account_number: The user's account number
    Returns:
        The user's ATM card details
    """
    print("INSIDE CARD DETAILS NODE")
    # Dummy database of card details
    card_details_db = {
        "08123854855": {"card_number": "1111-2222-3333-4444", "expiry_date": "12/25", "card_holder": "John Doe"},
        "987654321": {"card_number": "5555-6666-7777-8888", "expiry_date": "11/24", "card_holder": "Jane Smith"},
    }

    # Retrieve card details from the dummy database
    card_details = card_details_db.get(account_number, None)
    
    if card_details:
        return card_details
    else:
        return {"error": "Account number not found"}