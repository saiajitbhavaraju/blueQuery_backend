# File: core/config.py
# --- CORRECTED for new .env variables ---
import os
from dotenv import load_dotenv

load_dotenv()

# --- Oracle Database Configuration ---
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_HOST = os.getenv("ORACLE_HOST")
ORACLE_PORT = os.getenv("ORACLE_PORT")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE")
ORACLE_SCHEMA_OWNER = os.getenv("ORACLE_SCHEMA_OWNER")

# --- Firebase Configuration ---
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")

# --- Language Model Configuration ---
# These now correctly match your .env file
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

print("Configuration loaded successfully.")