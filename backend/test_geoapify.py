import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEOAPIFY_API_KEY")

if not api_key:
    print("ERROR: GEOAPIFY_API_KEY not found in backend/.env")
    exit(1)

params = {
    "categories": "entertainment.museum",
    "filter": "rect:73.5,15.8,74.5,14.8",
    "limit": "5",
    "apiKey": api_key,
}

url = f"https://api.geoapify.com/v2/places?{urllib.parse.urlencode(params)}"

try:
    req = urllib.request.Request(url, headers={"User-Agent": "TravelAgent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        status_code = response.getcode()
        data = json.loads(response.read().decode("utf-8"))

    features = data.get("features", [])
    print(f"Connection Status: SUCCESS (HTTP {status_code})")
    print(f"Results Count: {len(features)}")
    print("-" * 50)

    for idx, feature in enumerate(features[:5], start=1):
        props = feature.get("properties", {})
        name = props.get("name") or "Unnamed"
        address = props.get("formatted") or props.get("address_line2") or "No address provided"
        print(f"{idx}. {name}")
        print(f"   Address: {address}")

except urllib.error.HTTPError as e:
    print(f"Connection Status: FAILED (HTTP {e.code})")
    try:
        err_data = json.loads(e.read().decode("utf-8"))
        print(f"Error message: {err_data.get('message', e.reason)}")
    except Exception:
        print(f"Error reason: {e.reason}")
except urllib.error.URLError as e:
    print(f"Connection Status: FAILED (Network/URL Error: {e.reason})")
except TimeoutError:
    print("Connection Status: FAILED (Request timed out)")
except Exception as e:
    print(f"Connection Status: FAILED (Unexpected error: {str(e)})")

