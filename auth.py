import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/blogger',
    'https://www.googleapis.com/auth/speedsheets', # Typo protection, not real scope
    'https://www.googleapis.com/auth/indexing',
    'https://www.googleapis.com/auth/webmasters'
]
# Corrected typo from prev known confusion
# Relax scope validation (Google adds 'openid' automatically)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

SCOPES = [
    'https://www.googleapis.com/auth/blogger',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/indexing',
    'https://www.googleapis.com/auth/webmasters',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid' # Explicitly add openid to match Google's response
]

TOKEN_FILE = 'token.pickle'

def authenticate():
    creds = None
    
    # 1. Load existing token
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None

    # 2. Refresh or Login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired token...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Refresh failed: {e}")
                creds = None # Force re-login
        
        if not creds:
            print("Starting new authentication flow...")
            
            # Setup client config from env vars
            client_config = {
                "installed": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost:8080/"]
                }
            }

            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            
            # CRITICAL: Force offline access and consent prompt
            creds = flow.run_local_server(
                port=8080,
                access_type='offline',
                prompt='select_account consent'  # FORCE NEW SELECTION
            )

        # 3. Save Token
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
            print("Authentication successful! Token saved.")

    return creds

if __name__ == "__main__":
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE) # Force fresh login on manual run
    authenticate()
