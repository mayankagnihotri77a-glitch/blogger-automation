import os
import pickle
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = 'token.pickle'
BLOG_ID = os.getenv("BLOGGER_BLOG_ID")

def test_simple():
    if not os.path.exists(TOKEN_FILE):
        print("No token file.")
        return

    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)

    service = build('blogger', 'v3', credentials=creds)

    print(f"--- Attempting Minimal Post to Blog {BLOG_ID} ---")
    
    body = {
        'title': 'Minimal Verify Test',
        'content': 'This is a plain text post to verify API connectivity.',
        'labels': ['Test']
    }
    
    try:
        # Try DIRECT PUBLISH (Skip Draft)
        print("   Attempting DIRECT PUBLISH (isDraft=False)...")
        res = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"✅ SUCCESS! Created Post: {res.get('url')}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    input("\nPress Enter to close...")

if __name__ == "__main__":
    test_simple()
