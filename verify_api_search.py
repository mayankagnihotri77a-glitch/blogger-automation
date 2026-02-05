import os
import requests
from dotenv import load_dotenv

def verify_search():
    print("--- Verifying Google Image Search API ---")
    load_dotenv()
    
    key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    
    if not key:
        print("[!] GOOGLE_SEARCH_API_KEY is missing")
    else:
        print(f"[i] API Key: {key[:5]}...{key[-5:]}")
        
    if not cx:
        print("[!] GOOGLE_SEARCH_CX is missing")
    else:
        print(f"[i] CX ID: {cx}")
        
    if not key or not cx:
        return
        
    print("\n[i] Attempting to search for 'cat'...")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': 'cat',
        'cx': cx,
        'key': key,
        'searchType': 'image',
        'num': 1,
        'safe': 'active'
    }
    
    try:
        res = requests.get(url, params=params)
        data = res.json()
        
        if 'error' in data:
            print(f"[!] API Error: {data['error']['message']}")
            print(f"    Code: {data['error'].get('code')}")
            print(f"    Details: {data['error'].get('errors')}")
        elif 'items' in data:
            print("[+] Success! Found image:")
            print(f"    Link: {data['items'][0]['link']}")
            print(f"    Title: {data['items'][0]['title']}")
        else:
            print("[?] No items found, but no error reported.")
            print(f"    Response: {data}")
            
    except Exception as e:
        print(f"[!] Exception during request: {e}")

if __name__ == "__main__":
    verify_search()
