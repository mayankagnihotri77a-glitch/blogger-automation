import os
import time
import warnings
# Suppress warnings before importing the deprecated package
warnings.simplefilter(action='ignore', category=FutureWarning)
import google.generativeai as genai
import json

def generate_post(topic):
    # Load all available keys
    keys = []
    
    # 1. Check for comma-separated list
    main_key = os.getenv("GEMINI_API_KEY", "")
    if "," in main_key:
        keys.extend([k.strip() for k in main_key.split(",") if k.strip()])
    elif main_key:
        keys.append(main_key)
        
    # 2. Check for indexed keys (GEMINI_API_KEY_1, _2, etc.)
    i = 1
    while True:
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if not k: break
        keys.append(k.strip())
        i += 1
        
    if not keys:
        print("Missing Gemini API Key(s)")
        return None
        
    print(f"   [i] Loaded {len(keys)} Gemini API Keys for rotation.")

    # Retry parameters
    max_retries = 3
    retry_delays = [5, 10, 20] # Shorter delays since we have rotation
    
    current_key_idx = 0
    
    for attempt in range(max_retries * len(keys)): # Try enough times for all keys
        try:
            # Configure with current key
            current_key = keys[current_key_idx]
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
            
            # We remove response_mime_type="application/json" to get raw text
            response = model.generate_content(prompt)
            
            raw_text = response.text.strip()
            
            # Parse Delimiter Format
            if "|||SEPARATOR|||" in raw_text:
                parts = raw_text.split("|||SEPARATOR|||")
                if len(parts) >= 2:
                    title = parts[0].strip()
                    content = parts[1].strip()
                    # Cleanup markdown code blocks if model adds them
                    if content.startswith("```html"): content = content[7:]
                    if content.startswith("```"): content = content[3:]
                    if content.endswith("```"): content = content[:-3]
                    
                    return {"title": title, "content": content.strip()}
            
            # Fallback if separator missing (rare)
            print(f"[!] Warning: Separator missing. Trying heuristic parse.")
            lines = raw_text.split('\n')
            title = lines[0].strip()
            content = '\n'.join(lines[1:]).strip()
            return {"title": title, "content": content}
            
        except Exception as e:
            error_msg = str(e)
            # Check if it's a 429 rate limit error
            if "429" in error_msg or "Resource exhausted" in error_msg:
                print(f"[⚠️] Key {current_key[:5]}... hit rate limit (429).")
                
                # Rotate Key
                current_key_idx = (current_key_idx + 1) % len(keys)
                next_key = keys[current_key_idx]
                print(f"   [↻] Rotating to next key: {next_key[:5]}...")
                
                time.sleep(2) # Brief pause
                continue
            else:
                # Non-rate-limit error
                print(f"Gemini error: {e}")
                return None
    
    print("[!] All keys exhausted or max retries reached.")
    return None
