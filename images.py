import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_image(query):
    key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
    cx = os.getenv("GOOGLE_SEARCH_CX", "").strip()
    
    if not key or not cx:
        print("   [!] Missing Image Search Keys in environment")
        return None
        
    base_params = {
        'cx': cx, 'key': key,
        'searchType': 'image', 'num': 1, 'safe': 'active'
    }
    
    # Helper to execute search
    def search(q, size_param=None):
        p = base_params.copy()
        p['q'] = q
        if size_param:
            p['imgSize'] = size_param
            
        try:
            res = requests.get("https://www.googleapis.com/customsearch/v1", params=p).json()
            if 'error' in res:
                # Quota or permission error, don't spam retries
                print(f"   [!] Search API Error: {res['error']['message']}")
                return None
            
            items = res.get('items', [])
            if items:
                link = items[0]['link']
                if link.startswith('http'):
                    return link
        except Exception as e:
            print(f"   [!] Search Exception: {e}")
        return None

    # Strategy 1: Exact query, Large images (High Quality)
    # print(f"   [>] Searching (Large): {query[:40]}...")
    link = search(query, 'large')
    if link: return link
    
    # Strategy 2: Exact query, Any size
    print(f"   [i] No large images. Retrying with any size...")
    link = search(query, None)
    if link: return link
    
    # Strategy 3: Simplify Query (Remove after ':', '-', or truncating)
    # Common separators in titles: ":", " - ", "|"
    simplified_query = None
    for sep in [':', ' - ', '|']:
        if sep in query:
            simplified_query = query.split(sep)[0].strip()
            break
            
    if not simplified_query and len(query.split()) > 6:
        # Fallback: First 6 words
        simplified_query = " ".join(query.split()[:6])
        
    if simplified_query and simplified_query != query:
        print(f"   [i] Retrying with simplified query: '{simplified_query}'")
        link = search(simplified_query, 'large') # Try large first for simplified
        if link: return link
        
        link = search(simplified_query, None) # Then any size
        if link: return link
       
    # Strategy 4: Aggressive Simplification (First 3 words)
    # If we still haven't found anything, try very broad.
    msg_query = simplified_query if simplified_query else query
    words = msg_query.split()
    if len(words) > 3:
        aggressive_query = " ".join(words[:2]) # Just 2 words (e.g. "Lea Micheles")
        print(f"   [i] Retrying with aggressive query: '{aggressive_query}'")
        link = search(aggressive_query, 'large')
        if link: return link
        link = search(aggressive_query, None)
        if link: return link

    # Strategy 5: Nuclear Option (First Word Only)
    # If "Lea Micheles" fails, "Lea" usually works.
    if len(words) >= 1 and len(words[0]) > 2:
        nuclear_query = words[0]
        # remove possessive 's or similar if present (simple heuristic)
        if nuclear_query.lower().endswith("'s"): nuclear_query = nuclear_query[:-2]
        
        print(f"   [i] Retrying with nuclear query: '{nuclear_query}'")
        link = search(nuclear_query, 'large')
        if link: return link
        link = search(nuclear_query, None)
        if link: return link

    print(f"   [!] Failed to find image for: {query}")
    return None

# Deprecated/Removed Unsplash Fallback
# def get_unsplash_image(query): ...
