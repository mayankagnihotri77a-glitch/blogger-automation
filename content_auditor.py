

import os
import time
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import auth
import content # Use existing Gemini logic, might need tweak
import images

# Load environment variables from .env file
load_dotenv()

BLOG_ID = os.getenv("BLOG_ID") # Logic to fetch if missing

def count_words(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    return len(text.split())

def has_images(html):
    return "<img" in html

def rebuild_post(service, blog_id, post):
    title = post['title']
    print(f"   [Fix] Rebuilding: {title}...")
    
    # 1. Generate New Content (High Value)
    # We use a specialized prompt here, distinct from content.py
    # Using content.generate_post might be enough if we tweak the prompt there?
    # Better to ask Gemini explicitly for "Long Form AdSense Safe" here.
    
    new_data = content.generate_post(title) # Reuse for now, maybe custom prompt later
    if not new_data:
        print("   [!] Generation failed.")
        return False
    
    # CRITICAL: Add delay after API call to avoid rate limit bursts
    print("   [i] Waiting 2s after content generation...")
    time.sleep(2)
        
    html = new_data['content']
    
    # 2. Handle Images Intelligently
    # PRESERVE ALL existing images from the old post
    old_html = post.get('content', '')
    from bs4 import BeautifulSoup
    old_soup = BeautifulSoup(old_html, 'html.parser')
    existing_imgs = old_soup.find_all('img')
    
    # FILTER: Remove known broken images (Unsplash source deprecated)
    valid_existing_imgs = []
    has_broken_images = False
    
    for img in existing_imgs:
        src = img.get('src', '')
        # Check for Unsplash broken links or very small generic icons (sometimes happen)
        if "source.unsplash.com" in src or "images.unsplash.com" in src:
            print(f"   [-] Removing broken Unsplash image: {src[:30]}...")
            has_broken_images = True
            continue 
        # Check if it's a valid http link
        if not src.startswith('http'):
            print(f"   [-] Removing invalid image source: {src[:30]}...")
            continue
            
        valid_existing_imgs.append(str(img))

    print(f"   [i] Found {len(valid_existing_imgs)} valid existing images to preserve.")
    if has_broken_images:
        print("   [!] Logic: Will replace broken images by strictly fetching new ones.")

    # Determine how many new images we need to fetch (Minimum target: 2)
    # If we had broken images, we treat target as higher to ensure we fill the gaps
    target_images = 2
    existing_img_tags = valid_existing_imgs # Use the filtered list
    needed_new_images = max(0, target_images - len(existing_img_tags))
    
    new_img_tags = []
    used_urls = set()
    
    # Add existing images to used set to avoid re-fetching them (unlikely but good safety)
    for tag in existing_img_tags:
        soup_temp = BeautifulSoup(tag, 'html.parser')
        img_temp = soup_temp.find('img')
        if img_temp and img_temp.get('src'):
            used_urls.add(img_temp.get('src'))

    if needed_new_images > 0:
        print(f"   [i] Fetching {needed_new_images} new images to meet minimum requirement...")
        
        # Query variations to ensure different images
        variations = ["", " wallpaper", " visualization", " infographic", " background", " chart"]
        
        for i in range(needed_new_images):
            # Create distinct query
            variation = variations[i % len(variations)]
            search_query = f"{title}{variation}"
            
            img_url = images.get_image(search_query)
            
            # Check for duplicates or invalid
            if img_url and img_url not in used_urls:
                used_urls.add(img_url)
                
                # Create styled image tag
                new_tag = f'<img src="{img_url}" style="width:100%; border-radius:10px; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="{title} image {i+1}">'
                new_img_tags.append(new_tag)
                print(f"   [+] Fetched new image: {img_url[:30]}...")
            elif img_url:
                 print(f"   [!] Skipped duplicate image: {img_url[:30]}...")
            else:
                print(f"   [!] Failed to fetch image {i+1}")

    # Combine all images available
    all_images_to_insert = existing_img_tags + new_img_tags
    
    # Logic to insert them into the new HTML
    # Position 1: Replace [IMAGE] placeholder or Top
    # Position 2: Middle of content
    # Position 3+: Evenly distributed
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Helper to insert image after a paragraph
    def insert_after_paragraph(img_html, paragraph_index, soup_obj):
        paragraphs = soup_obj.find_all('p')
        if paragraphs and len(paragraphs) > paragraph_index:
            p = paragraphs[paragraph_index]
            new_tag = BeautifulSoup(img_html, 'html.parser')
            p.insert_after(new_tag)
            return True
        return False

    # Insert Image 1 (First existing or First new)
    if all_images_to_insert:
        first_img = all_images_to_insert.pop(0)
        if '[IMAGE]' in html:
            html = html.replace('[IMAGE]', first_img)
            print("   [+] Placed Image 1 at placeholder position")
        else:
            # If no placeholder, insert at top (after H1 if exists, else prepend)
            # Actually prepend to body is easiest for "start"
            html = first_img + html
            print("   [+] Placed Image 1 at start")
            
    # Insert remaining images
    if all_images_to_insert:
        # Re-parse because we modified html string above (text replace)
        # But wait, if we use soup for everything it's cleaner.
        # Let's stick to simple text replace for the first one for speed/reliability with the placeholder
        # Now use soup for the rest
        soup = BeautifulSoup(html, 'html.parser')
        paragraphs = soup.find_all('p')
        p_count = len(paragraphs)
        
        imgs_remaining = len(all_images_to_insert)
        
        if p_count > 0:
            # Calculate intervals
            # If 1 image remaining: put in middle (index p_count // 2)
            # If multiple: distribute
            
            for i, img_code in enumerate(all_images_to_insert):
                # Distribute evenly. 
                # Example: 10 headings. 2 images. 
                # pos = (i + 1) * (count / (imgs + 1))
                # i=0: 1 * (10/3) = 3.3 -> 3
                # i=1: 2 * (10/3) = 6.6 -> 7
                idx = int((i + 1) * (p_count / (imgs_remaining + 1)))
                
                # Create tag object
                # Note: BeautifulSoup parsing of the img_code might add <html><body>
                # So we extract the tag direct
                img_soup = BeautifulSoup(img_code, 'html.parser')
                img_tag_to_insert = img_soup.find('img')
                
                if img_tag_to_insert:
                    if idx < len(paragraphs):
                        paragraphs[idx].insert_after(img_tag_to_insert)
                        print(f"   [+] Placed Image {i+2} after paragraph {idx}")
                    else:
                        # Append to end if calculation off
                        soup.append(img_tag_to_insert)
        
        # Get final HTML
        html = str(soup)

    # Clean up any leftover [IMAGE] if we didn't have any images (rare)
    html = html.replace("[IMAGE]", "")
             
    # 3. Update Blogger
    try:
        post['content'] = html
        post['updated'] = time.strftime('%Y-%m-%dT%H:%M:%S.000-07:00') # Update timestamp?
        # Actually Blogger handles timestamp updates usually.
        
        service.posts().update(blogId=blog_id, postId=post['id'], body=post).execute()
        print(f"   [+] Successfully updated: {title}")
        return True
    except Exception as e:
        print(f"   [!] Update failed: {e}")
        return False

def run_audit():
    print("--- Starting Content Quality Audit (AdSense Fixer) ---")
    
    # CRITICAL: Wait 60s on startup to ensure rate limit window has reset
    print("[...] Waiting 60 seconds to ensure rate limit window is clear...")
    print("     (If you just ran this script, the API needs time to reset)")
    time.sleep(60)
    print("[+] Ready to begin!\n")
    
    creds = auth.authenticate()
    service = build('blogger', 'v3', credentials=creds)
    
    # Initialize counter
    fixed_count = 0
    
    # Get Blog ID
    if not BLOG_ID:
        # Fetch first blog
        blogs = service.blogs().listByUser(userId='self').execute()
        my_blog_id = blogs['items'][0]['id']
        print(f"[i] Using Blog ID: {my_blog_id} ({blogs['items'][0]['name']})")
    else:
        my_blog_id = BLOG_ID
        
    # List Posts
    # List Posts with Pagination
    try:
        page_token = None
        total_scanned = 0
        total_limit = 200 # Safety limit to avoid infinite loops, scan last 200 posts
        
        while total_scanned < total_limit:
            posts = service.posts().list(
                blogId=my_blog_id, 
                maxResults=50, 
                status=["LIVE"],
                pageToken=page_token
            ).execute()
            
            items = posts.get('items', [])
            if not items:
                print("[i] No more posts found.")
                break
                
            print(f"[i] Scanning batch... (Posts {total_scanned+1} to {total_scanned+len(items)})")
            
            for post in items:
                title = post['title']
                content_html = post.get('content', '')
                
                w_count = count_words(content_html)
                has_img = has_images(content_html)
                
                is_low_value = False
                reasons = []
                
                # Google AdSense 2026 Compliance Checks
                # Minimum word count (800-1500 recommended)
                if w_count < 1000:
                    is_low_value = True
                    reasons.append(f"Too Short ({w_count} words, need 1000+)")
                
                # Must have images for engagement
                if not has_img:
                    is_low_value = True
                    reasons.append("No Images")
                    
                # E-E-A-T: Check for Expert Analysis/Unique Perspective
                has_analysis = any(keyword in content_html for keyword in ["Analysis", "Why This Matters", "Our Perspective", "Expert"])
                if not has_analysis:
                    is_low_value = True
                    reasons.append("Missing Expert Analysis (E-E-A-T)")
                
                # Check for structured content (FAQ, Key Takeaways)
                has_structure = any(keyword in content_html for keyword in ["FAQ", "Key Takeaways", "What's Next"])
                if not has_structure:
                    is_low_value = True
                    reasons.append("Missing Structured Sections (FAQ/Takeaways)")
                
                # Check for proper HTML headings (H2, H3)
                has_headings = "<h2" in content_html or "<h3" in content_html
                if not has_headings:
                    is_low_value = True
                    reasons.append("Poor Formatting (No H2/H3 headings)")

                if is_low_value:
                    print(f"[Low Value] {title} -> {', '.join(reasons)}")
                    success = rebuild_post(service, my_blog_id, post)
                    if success:
                        fixed_count += 1
                        print(f"[+] Fixed {fixed_count} posts so far")
                        print("[i] Sleeping 5s between posts for safe rate limiting...")
                        time.sleep(5)  # Conservative: ~10/min accounting for internal delays
                    else:
                        print("[!] Fix failed. Sleeping 15s before retry...")
                        time.sleep(15)
                    
                    # Batch limit: 30 posts per run (safe daily quota management)
                    if fixed_count >= 30:
                        print(f"\n[!] Reached batch limit (30 posts). Run again for next batch.")
                        print(f"    Total fixed this run: {fixed_count}")
                        return
                else:
                    print(f"[OK] {title} ({w_count} words)")
            
            total_scanned += len(items)
            page_token = posts.get('nextPageToken')
            if not page_token:
                break
                
        print(f"\nAudit Complete. Scanned {total_scanned} posts. Fixed {fixed_count} posts.")
        
    except Exception as e:
        print(f"[!] Listing failed: {e}")

if __name__ == "__main__":
    run_audit()
