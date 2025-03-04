import json
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from Tools.FAQ import retriever_tool
from Tools.HISTORY import retrieve_transaction_history_tool
from Tools.TICKET import create_ticket_tool
from Tools.BLOCK import block_account_tool, block_card_tool
from Tools.ACCOUNT import retrieve_account_tool

import streamlit as st

load_dotenv()

# Load the environment variables
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

with open('bank_settings.json', 'r') as f:
    settings = json.load(f)

BANK_NAME = settings.get("bank_name")
PROMPT = settings.get("prompt")

if not PROMPT:
    PROMPT = "You are a helpful Assistant that responds to user inquiries"


llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", api_key=GOOGLE_API_KEY)

web_search_tool = TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)

tools = [
    web_search_tool,
    retriever_tool,
    retrieve_transaction_history_tool,
    create_ticket_tool,
    block_account_tool,
    block_card_tool,
    retrieve_account_tool,
]

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "{prompt} {bank_name}. "
            "Ensure you are always conversational, professional and use a friendly tone. "
            "Use the provided tools to assist the user's queries."
            "When using the transaction history tool only, get the user's account number from the user any other tool does not require user's account number. "
            "Use the create ticket tool only when the user has a complaint, and you can't resolve it. Ensure the user's account number is shared with in ticket."
            "When using the create ticket tool, The subject and body of the ticket must be well detailed and formated. The body should be a detailed explanation of the issue and it must also contain the account number of the user."
            "Don't always rush to submit tickets, always get the complete details of the issue before submitting a ticket. If you need to inetract with the other tools please do just ensure you have the full details."
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If a search comes up empty, expand your search before giving up."
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now, bank_name=BANK_NAME, prompt=PROMPT)
llm_agent = primary_assistant_prompt | llm.bind_tools(tools)


# Setting up the graph state
class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    return {"messages": [llm_agent.invoke({"messages": state["messages"]})]}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

graph_builder.add_node("tools", ToolNode(tools))

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": BANK_NAME}}

# while True:
#     user_input = input("User: ")
#     if user_input.lower() in ["quit", "exit", "q"]:
#         print("Goodbye!")
#         break

#     event = graph.invoke({"messages": ("user", user_input)}, config)
#     print("Assistant:", event["messages"][-1].content)

def AvniCoreAI(user_input: str):
    try:
        event = graph.invoke({"messages": ("user", user_input)}, config)
        return event["messages"][-1].content
    except Exception as e:
        print(f"Error: {e}")
        return "Ops, sorry something went wrong please refresh the browser and try again, so sorry for the inconvenience"