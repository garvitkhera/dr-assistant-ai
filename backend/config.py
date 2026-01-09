import os
from dotenv import load_dotenv

# Load .env file if it exists (local development)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials - set SUPABASE_URL and SUPABASE_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key - set OPENAI_API_KEY")
