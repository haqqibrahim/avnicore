import os
import json
import streamlit as st

# Define constants
SETTINGS_FILE = "bank_settings.json"
DATA_FOLDER = "data"

# Ensure the data folder exists
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

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

st.title("Avnicore AI Setup")

# Load any previously saved settings
settings = load_settings()

# Input fields with pre-populated values if available
bank_name = st.text_input("Bank Name", value=settings.get("bank_name", ""), placeholder="Enter the bank name")
url = st.text_input("URL", value=settings.get("url", ""), placeholder="Enter the bank's URL")
prompt = st.text_area("Prompt", value=settings.get("prompt", ""), placeholder="Enter the prompt for the AI")

# File uploader for the document
uploaded_file = st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])

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
        # Save the file path in settings
        settings["document"] = file_path
    else:
        settings["document"] = None

    # Save settings to the JSON file
    save_settings(settings)
    st.success("Settings saved and file stored in the data folder!")

if st.button("Reset Settings"):
    reset_settings()
    st.success("Settings have been reset!")