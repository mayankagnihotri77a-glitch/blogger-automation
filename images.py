import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_image(query):
    key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
    cx = os.getenv("GOOGLE_SEARCH_CX", "").strip()
    
    # Debug: Print what we're getting from environment
    print(f"   [DEBUG] API Key loaded: {'Yes' if key else 'No'} ({len(key)} chars)")
    print(f"   [DEBUG] CX loaded: {'Yes' if cx else 'No'} ({len(cx)} chars)")
    
    if not key or not cx:
        print("   [!] Missing Image Search Keys in environment")
        return None
        
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query, 'cx': cx, 'key': key,
        'searchType': 'image', 'num': 1, 'safe': 'active',
        'imgSize': 'large' # Ensure high quality
    }
    
    try:
        res = requests.get(url, params=params).json()
        if 'error' in res:
            msg = res['error']['message']
            print(f"   [!] Google Image Search error: {msg}")
            # NO FALLBACK - User requested strict Google Image Search
            return None
            
        items = res.get('items', [])
        if items:
            link = items[0]['link']
            # Basic validation to ensure it's a real image URL
            if link.startswith('http'):
                return link
    except Exception as e:
        print(f"   [!] Image fetch exception: {e}")
        
    return None

# Deprecated/Removed Unsplash Fallback
# def get_unsplash_image(query): ...
