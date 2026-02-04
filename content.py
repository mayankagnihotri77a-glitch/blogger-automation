import warnings
warnings.simplefilter("ignore", category=FutureWarning)
import google.generativeai as genai
import os
import time
import random
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted
from datetime import datetime

load_dotenv()

# 1. Load ALL available Keys
API_KEYS = []
# Check for main key and up to 5 alternatives
if os.getenv("GEMINI_API_KEY"): API_KEYS.append(os.getenv("GEMINI_API_KEY"))
for i in range(2, 6):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key: API_KEYS.append(key)

if not API_KEYS:
    print("CRITICAL WARNING: No GEMINI_API_KEY found.")

# 2. Verified Model List (Based on your Account Access)
MODEL_NAMES = [
    # Top Priority (Newest & Best)
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    
    # Secondaries
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite-preview",

    # Fallbacks
    "gemini-flash-latest",
]

def generate_blog_post(topic_data, news_context=None):
    """Generates content trying Multiple Keys AND Multiple Models."""
    
    topic = topic_data['title']
    google_trends_context = topic_data['snippet']
    traffic = topic_data['traffic']
    
    today_date = datetime.now().strftime("%B %d, %Y")

    print(f"Generated content for: {topic} (Date: {today_date})")

    # Format News Context for the LLM
    news_text_block = ""
    if news_context:
        news_text_block = "LATEST LIVE NEWS (FACTUAL SOURCE):\n"
        for i, item in enumerate(news_context):
            news_text_block += f"{i+1}. TITLE: {item['title']}\n   SOURCE: {item['source']} ({item['date']})\n   SNIPPET: {item['snippet']}\n\n"
    else:
        news_text_block = "No live news available. Rely on general knowledge (Risk of being outdated)."

    # UPDATED PROMPT FOR ADSENSE APPROVAL (2026 E-E-A-T Compliance)
    prompt = f"""
    You are a senior investigative journalist with deep expertise in breaking news. Write a COMPREHENSIVE, ORIGINAL article about "{topic}".
    
    **CRITICAL: Google AdSense 2026 Compliance (E-E-A-T Principles)**
    This article MUST demonstrate:
    - **Experience**: Write from a knowledgeable perspective, as if you've extensively covered this topic
    - **Expertise**: Show deep understanding, provide context, explain implications
    - **Authoritativeness**: Use confident, informed language; back claims with the news context below
    - **Trustworthiness**: Be factual, balanced, verify against provided sources
    
    **CRITICAL SOURCE MATERIAL:**
    {news_text_block}
    
    **CONTEXT FROM GOOGLE TRENDS:**
    {google_trends_context}
    
    Current Trending Traffic: {traffic}
    Current Date: {today_date}

    **MANDATORY Structure (All sections REQUIRED):**
    1. **Headline**: Inside <h1> tags - compelling, SEO-optimized, factual
    2. **Key Takeaways**: 4-5 bullet points at the very top (use <ul><li>)
    3. **Date/Location**: Start next paragraph with "NEW YORK – {today_date}" style dateline
    4. **Introduction** (no header): 2-3 paragraphs explaining why this matters NOW
    5. **The Full Story** (H2): Comprehensive breakdown with <h3> subsections for:
       - Background/Context
       - Key Developments
       - Impact Analysis
    6. **Expert Perspective** (H2): YOUR unique insights - explain WHY this matters beyond the facts, connect to broader trends
    7. **What's Next** (H2): Future implications, what to watch for
    8. **FAQ** (H2): 5-7 common questions, each as <h3> with detailed answers
    9. **Bottom Line** (H2): Final takeaway paragraph
    
    **Technical Requirements:**
    - **No placeholders** like [Date], [Location]. Omit if unknown.
    - **Length**: 1200-1500 words minimum
    - **Formatting**: STRICT HTML. Short paragraphs (2-4 sentences). Use <h2>, <h3>, <p>, <ul>, <li>, <b>. NO Markdown.
    - **AdSense Friendly**: Each paragraph should add unique value, not repeat information
    - **Image Placeholder**: Insert "[IMAGE]" right after Key Takeaways section
    
    **SEO Params**:
    - Provide "LABELS: ..." at the end (3-5 relevant tags)
    - Provide "DESCRIPTION: ..." at the end (max 150 chars)
    
    Tone: Professional, authoritative, engaging. Write as a human expert, not a bot.
    """

    # Loop through Keys first (Spread load)
    # We shuffle keys simply or try sequentially
    
    for key_index, api_key in enumerate(API_KEYS):
        # Configure with this key
        genai.configure(api_key=api_key)
        
        # Try models with this key
        for model_name in MODEL_NAMES:
            # print(f"   [Attempt] Key #{key_index+1} | Model: {model_name}...") # Reduced verbosity
            
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = response.text
                
                # Parse output
                # Clean up markdown fences if present
                text = text.replace("```html", "").replace("```", "").strip()
                
                parts = text.split("LABELS:")
                body_content = parts[0].strip()
                
                # Fallback: Convert Markdown to HTML if model ignored instructions
                if "###" in body_content or "**" in body_content:
                    import re
                    # Convert headers ### -> <h2>
                    body_content = re.sub(r'###\s*(.+)', r'<h2>\1</h2>', body_content)
                    body_content = re.sub(r'##\s*(.+)', r'<h2>\1</h2>', body_content)
                    # Convert bold **text** -> <b>text</b>
                    body_content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', body_content)
                    
                labels_part = parts[1].split("DESCRIPTION:")[0].strip() if len(parts) > 1 else "News, US, Trending"
                labels = [l.strip() for l in labels_part.split(',')]
                
                if "DESCRIPTION:" in text:
                    raw_desc = text.split("DESCRIPTION:")[1].strip()
                    # TRUNCATE to 150 chars just in case model ignores limit (User strict requirement)
                    description = raw_desc[:145] + "..." if len(raw_desc) > 150 else raw_desc
                else:
                    description = f"Breaking news update: {topic}."[:150]

                # Fallback title if regex fails
                title = f"{topic.title()}: Breaking News and Updates"
                
                if "<h1>" in body_content:
                    import re
                    m = re.search(r'<h1>(.*?)</h1>', body_content, re.IGNORECASE)
                    if m:
                        title_extracted = m.group(1).strip()
                        # Clean up if model put quotes around it
                        title = title_extracted.replace('"', '').replace("'", "")
                        body_content = body_content.replace(m.group(0), "")
                
                print(f"   [SUCCESS] Generated with {model_name}. Title: {title}")
                return {
                    "title": title,
                    "content": body_content,
                    "labels": labels,
                    "description": description
                }

            except ResourceExhausted:
                print(f"   [!] Quota LIMIT on Key #{key_index+1} / {model_name}. Switching...")
                continue 
            except Exception as e:
                # 404 means model not found for this key/version
                if "404" in str(e):
                    continue
                elif "429" in str(e):
                    print(f"   [!] Rate Limit (429). Switching...")
                    continue
                else:
                    print(f"   [x] Error with {model_name}: {e}")
                    continue
                    
    print("[x] ALL KEYS AND MODELS FAILED.")
    return None

if __name__ == "__main__":
    # Test
    dummy = {'title': 'Solar Eclipse 2024', 'snippet': 'Millions watch total solar eclipse.', 'traffic': '5M+'}
    print(generate_blog_post(dummy))
