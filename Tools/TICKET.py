import requests
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel

from langchain.tools import tool

load_dotenv()

ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
ZENDESK_API_KEY = os.getenv("ZENDESK_API_KEY")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")

class CreateTicketSchema(BaseModel):
    subject: str
    body: str

@tool(args_schema=CreateTicketSchema)
def create_ticket_tool(subject, body):
    """"
    Tool to create a ticket
    Args: 
        subject: The subject of the ticket 
        body: The body of the ticket

    Returns:
        The response from the Zendesk API showing the created ticket
    """
    # Construct the URL for the Zendesk ticket API endpoint
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json"

    # Define the ticket details
    ticket_data = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": body
            }
        }
    }

    # Set the headers to specify JSON content
    headers = {"Content-Type": "application/json"}

    # The authentication requires your email appended with '/token' and your API token
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_KEY)

    # Make the POST request to create the ticket
    response = requests.post(url, headers=headers, data=json.dumps(ticket_data), auth=auth)

    # Check the response status code
    if response.status_code == 201:
        print("Ticket created successfully!")
    else:
        print("Failed to create ticket.")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(response.text)

# Example usage:
# create_ticket("yoursubdomain", "youremail@example.com", "your_api_token", "Test Ticket from Python", "This is a test ticket created via the Zendesk API using Python.")
