import streamlit as st
from V1 import AvniCoreAI
from concurrent.futures import ThreadPoolExecutor

st.title("Customer Support Chatbot")
st.write("Welcome to the AvniCore AI Customer Support Chatbot.")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Initialize conversation history in session state if not already present
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

# Sidebar: Option to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state["chat_messages"] = []

def main():
    # Display chat messages stored in session state
    for message in st.session_state["chat_messages"]:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
    
    # Main chat interface
    user_input = st.chat_input("How can I help?")
    if user_input:
        # Append and display the user's message
        st.session_state["chat_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(user_input)
        
        # Get the AI response asynchronously using ThreadPoolExecutor
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            reason = "AvniCore AI is reasoning, please wait..."
            message_placeholder.markdown(reason)
            
            # Run the AI function in a separate thread to avoid blocking
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(AvniCoreAI, user_input=user_input)
                full_response = future.result()
            
            message_placeholder.markdown(full_response)
        
        # Append the AI's response to session state
        st.session_state["chat_messages"].append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
