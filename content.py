import os
import time
import warnings
# Suppress warnings before importing the deprecated package
warnings.simplefilter(action='ignore', category=FutureWarning)
import google.generativeai as genai
import json

def generate_post(topic):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Missing Gemini API Key")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
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
    
    
    # Retry with exponential backoff for rate limit errors
    max_retries = 3
    retry_delays = [30, 60, 120]  # 30s, 1min, 2min
    
    for attempt in range(max_retries):
        try:
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
                if attempt < max_retries - 1:
                    wait_time = retry_delays[attempt]
                    print(f"[⚠️] Rate limit hit. Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Gemini error after {max_retries} retries: {e}")
                    return None
            else:
                # Non-rate-limit error
                print(f"Gemini error: {e}")
                return None
    
    return None
    
    return None
