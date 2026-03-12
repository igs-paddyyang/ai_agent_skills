import os
from google import genai
from dotenv import load_dotenv

def main() -> None:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("No API Key")
        return

    client = genai.Client(api_key=api_key)
    try:
        for m in client.models.list():
            print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    main()
