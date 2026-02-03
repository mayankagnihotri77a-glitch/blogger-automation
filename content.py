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
    
    prompt = f"""
    You are a senior investigative journalist with deep expertise in breaking news. Write a COMPREHENSIVE, ORIGINAL article about: "{topic}".
    
    **CRITICAL: Google AdSense 2026 Compliance (E-E-A-T Principles)**
    To bypass "Low Value Content" filters, this article MUST demonstrate:
    - **Experience**: Include specific examples, case studies, or historical parallels. Avoid generic statements.
    - **Expertise**: defined by depth. Explain *mechanisms*, not just results. Use industry terminology correctly.
    - **Authoritativeness**: Adopt a confident, decisive tone. 
    - **Trustworthiness**: Present multiple viewpoints where applicable, then synthesize a concluded expert opinion.
    - **Originality**: Provide a unique angle or "contrarian" insight that isn't found in generic summaries.
    
    **MANDATORY Structure (All sections REQUIRED):**
    1. **Title (H1)**: Compelling, SEO-optimized, factual headline
    2. **Key Takeaways**: 4-5 bullet points summarizing main insights (use <ul>/<li>)
    3. **[IMAGE]** placeholder (place IMMEDIATELY after Key Takeaways)
    4. **Introduction**: fast-paced context. Why this matters NOW.
    5. **The Deep Dive** (H2): Who/what/when/where/why breakdown. Use <h3> subsections for readability.
    6. **Expert Analysis & Implications** (H2): The MOST IMPORTANT section. Explain the "So What?". How does this affect the industry/world in 6-12 months? 
    7. **Future Outlook** (H2): Prediction based on current data.
    8. **FAQ** (H2): 5-7 distinct questions that a user would actually ask (use <h3> for each question).
    9. **Bottom Line** (H2): Final summary verdict.
    
    **Technical Requirements:**
    - **Minimum Length**: 1200 words (aim for 1500+). Do not Hallucinate word count, actually write long content.
    - **Formatting**: Short paragraphs (2-4 sentences each) for mobile readability.
    - **No placeholders**: Never write [Date], [Location], etc. - omit if unknown.
    - **HTML Only**: Use <h2>, <h3>, <p>, <ul>, <li>, <strong>, <em>. NO markdown, NO <html>/<body> tags.
    
    **Output Format**: 
    - First line: The Title
    - Second line: "|||SEPARATOR|||"
    - Rest of text: The HTML Content
    
    **CRITICAL**: 
    - Do NOT output JSON. 
    - Ensure the separator "|||SEPARATOR|||" is exact.
    
    Tone: Professional, authoritative, slightly provocative (financial/tech journalism style).
    """

    # Models to try (in order of preference/speed)
    # 2.0 Flash is generally fastest -> 1.5 Flash is reliable -> 1.5 Pro is high quality fallback
    models_to_try = [
        'gemini-2.0-flash', 
        'gemini-1.5-flash', 
        'gemini-1.5-pro',
        'gemini-2.0-flash-lite'
    ]
    
    current_key_idx = 0
    current_model_idx = 0
    
    # Try all keys x all models
    total_attempts = len(keys) * len(models_to_try) * max_retries
    
    for attempt in range(total_attempts):
        try:
            # Configure with current key
            current_key = keys[current_key_idx]
            current_model_name = models_to_try[current_model_idx]
            
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel(current_model_name)
            
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
                print(f"[⚠️] {current_model_name} with Key {current_key[:5]}... hit limit.")
                
                # Logic: Switch Model first, then Key if all models fail for that key?
                # Simpler: Just rotate through the cartesian product sequentially or random?
                # Let's rotate Model first (stay on same key), then rotate Key.
                
                current_model_idx += 1
                if current_model_idx >= len(models_to_try):
                    current_model_idx = 0
                    current_key_idx = (current_key_idx + 1) % len(keys)
                    print(f"   [↻] Switching to next KEY: {keys[current_key_idx][:5]}...")
                
                print(f"   [↻] Retrying with Model: {models_to_try[current_model_idx]}...")
                
                time.sleep(2) # Brief pause
                continue
            else:
                # Non-rate-limit error
                print(f"Gemini error: {e}")
                return None
    
    print("[!] All keys exhausted or max retries reached.")
    return None
