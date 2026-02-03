import os
import pickle
import requests
from google.auth.transport.requests import Request

TOKEN_FILE = 'token.pickle'

def check_token_truth():
    if not os.path.exists(TOKEN_FILE):
        print("No token file.")
        return

    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)

    if creds.expired and creds.refresh_token:
        print("Token expired, refreshing...")
        creds.refresh(Request())

    access_token = creds.token
    print(f"Checking token: {access_token[:10]}...")

    # Query Google's tokeninfo endpoint
    resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}")
    
    if resp.status_code != 200:
        print(f"Error checking token: {resp.text}")
        return

    data = resp.json()
    print("\n--- GOOGLE SERVER SAYS ---")
    print(f"Issued To: {data.get('audience')}")
    print(f"Scopes Granted:")
    scopes = data.get('scope', '').split(' ')
    for s in scopes:
        print(f" - {s}")

    if "https://www.googleapis.com/auth/blogger" in scopes:
        print("\n[SUCCESS] SERVER CONFIRMS: You HAVE Blogger Write access.")
        print("If you still get 403, your ACCOUNT or IP is flagged/blocked by Blogger Anti-Spam.")
    else:
        print("\n[FAIL] SERVER SAYS: You DO NOT have Blogger access.")
        print("The unexpected happened: You might have unchecked the box, or the scope was rejected.")

    input("\nPress Enter to close...")

if __name__ == "__main__":
    try:
        check_token_truth()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to close (Error)...")
