import os
import sys
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Suppress benign internal SDK warning regarding Automatic Function Calling (AFC)
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

print("=" * 65)
print("[1/5] Script started: Initializing Gemini connection test...")
print("=" * 65)

# 1. Locate and load backend/.env
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    print(f"❌ Error: .env file not found at {env_path}")
    sys.exit(1)

load_dotenv(dotenv_path=env_path)

# 2. Read and validate API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or not api_key.strip():
    print("❌ Error: GEMINI_API_KEY not found or empty in backend/.env")
    print("   Please open backend/.env and add: GEMINI_API_KEY=your_key")
    sys.exit(1)

print(f"[2/5] API key detected successfully (length: {len(api_key.strip())} chars, secret hidden).")

# 3. Select Gemini model
# Recommended fast models: 'gemini-3.1-flash-lite' (ultra-fast ~1s) or 'gemini-3.5-flash' (~2-5s)
default_model = "gemini-3.1-flash-lite"
configured_model = os.getenv("GEMINI_MODEL")

if configured_model:
    model = configured_model.strip()
    print(f"[3/5] Target model configured via environment: '{model}'")
else:
    model = default_model
    print(f"[3/5] Target model using recommended default: '{model}'")

# 4. Create Gemini client
try:
    client = genai.Client(api_key=api_key.strip())
    print("[4/5] Gemini client initialized successfully.")
except Exception as client_err:
    print(f"❌ Failed to initialize Gemini client: {client_err}")
    sys.exit(1)

# 5. Send generation request
prompt_text = "Explain what a virtual travel agent does in two sentences."
print(f"\n[5/5] Sending request to Gemini API...")
print(f"      Prompt: \"{prompt_text}\"")
print(f"      Connecting to Google AI endpoint for model '{model}'...", flush=True)

start_time = time.time()

try:
    response = client.models.generate_content(
        model=model,
        contents=prompt_text,
    )
    elapsed = time.time() - start_time

    print(f"\n Response received successfully in {elapsed:.2f} seconds!")
    print("=" * 65)
    print("GEMINI RESPONSE:")
    print("=" * 65)
    if response and response.text:
        print(response.text.strip())
    else:
        print("(Empty response text received)")
    print("=" * 65)

except errors.APIError as api_err:
    elapsed = time.time() - start_time
    print(f"\n❌ Gemini API returned an error after {elapsed:.2f}s:")
    print(f"   Status Code: {getattr(api_err, 'code', 'Unknown')}")
    print(f"   Message: {getattr(api_err, 'message', api_err)}")

except Exception as error:
    elapsed = time.time() - start_time
    print(f"\n❌ Gemini request failed after {elapsed:.2f}s:")
    print(f"   Error Type: {type(error).__name__}")
    print(f"   Details: {error}")
