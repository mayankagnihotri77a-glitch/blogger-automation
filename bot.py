import time
import os
import argparse
from googleapiclient.discovery import build
import auth
import trends
import content
import images
import email_poster

# ... (Previous imports)

def run_batch():
    # Authenticate mainly for Indexing API (optional)
    creds = auth.authenticate()
    
    # We don't strictly need blogger_service for posting anymore
    # but we might keep creds for Indexing if that works.
    
    topics = trends.get_trends()
    if not topics: return

    for topic in topics:
        print(f"Processing: {topic['title']}")
        
        # content
        post_data = content.generate_post(topic['title'])
        if not post_data: continue
        
        # image
        img_url = images.get_image(topic['title'])
        
        # html assembly
        html = post_data['content']
        # html assembly
        html = post_data['content']
        
        # --- ROBUST IMAGE LOGIC (Ported from content_auditor.py) ---
        from bs4 import BeautifulSoup
        
        # We need at least 2 images
        target_images = 2
        new_img_tags = []
        used_urls = set()
        
        # Query variations to ensure different images
        variations = ["", " wallpaper", " visualization", " infographic", " background", " chart"]

        print(f"   [i] Fetching {target_images} images for new post...")
        for i in range(target_images):
            # Create distinct query
            variation = variations[i % len(variations)]
            search_query = f"{topic['title']}{variation}"
            
            img_url = images.get_image(search_query)
            
            if img_url and img_url not in used_urls:
                used_urls.add(img_url)
                # Create styled image tag
                new_tag = f'<img src="{img_url}" style="width:100%; border-radius:10px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="{topic["title"]} image {i+1}">'
                new_img_tags.append(new_tag)
                print(f"   [+] Fetched image {i+1}: {img_url[:30]}...")
            else:
                 print(f"   [!] Failed/Duplicate image {i+1}")

        # Insert images into HTML
        # Image 1: Placeholder or Top
        # Image 2+: Distributed
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Insert Image 1
        if new_img_tags:
            first_img = new_img_tags.pop(0)
            if "[IMAGE]" in html:
                html = html.replace("[IMAGE]", first_img)
            else:
                # Prepend if no placeholder
                html = first_img + html
                
        # Insert remaining images
        if new_img_tags:
            soup = BeautifulSoup(html, 'html.parser')
            paragraphs = soup.find_all('p')
            p_count = len(paragraphs)
            imgs_remaining = len(new_img_tags)
            
            if p_count > 0:
                for i, img_code in enumerate(new_img_tags):
                    # Middle distribution
                    idx = int((i + 1) * (p_count / (imgs_remaining + 1)))
                    
                    img_soup = BeautifulSoup(img_code, 'html.parser')
                    img_tag_to_insert = img_soup.find('img')
                    
                    if img_tag_to_insert:
                        if idx < len(paragraphs):
                            paragraphs[idx].insert_after(img_tag_to_insert)
                        else:
                            soup.append(img_tag_to_insert)
            html = str(soup)
            
        # Clean up any leftover [IMAGE]
        html = html.replace("[IMAGE]", "")
                
        # --- POST VIA EMAIL (Reliable Fallback) ---
        success = email_poster.send_post_via_email(post_data['title'], html)
        
        if success:
            print(f"Posted: {post_data['title']}")
            # Indexing might fail if we don't have the URL immediately.
            # Blogger Email posting is async, so we don't get the URL back instantly.
            # We can skip instant indexing for now, or assume it will be indexed naturally.
            print("Note: Indexing skipped because Email Posting doesn't return immediate URL.")
            
def main():
    print("Bot v2 Started.")
    while True:
        run_batch()
        print("Waiting 2 hours...")
        time.sleep(7200)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to close window...")
