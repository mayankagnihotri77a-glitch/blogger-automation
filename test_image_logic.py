
from bs4 import BeautifulSoup
import re

# Mock Logic being tested
def process_images_mock(html, old_html, title="Test Title"):
    print(f"\n--- Testing Post: {title} ---")
    
    # PRESERVE existing images
    old_soup = BeautifulSoup(old_html, 'html.parser')
    existing_imgs = old_soup.find_all('img')
    existing_img_tags = [str(img) for img in existing_imgs]
    print(f"   [i] Found {len(existing_img_tags)} existing images.")

    target_images = 2
    needed_new_images = max(0, target_images - len(existing_img_tags))
    
    new_img_tags = []
    if needed_new_images > 0:
        print(f"   [i] Fetching {needed_new_images} new images...")
        for i in range(needed_new_images):
            # Mock URL
            img_url = f"http://mock.url/image_{i+1}.jpg"
            new_tag = f'<img src="{img_url}" style="width:100%;" alt="{title} image {i+1}">'
            new_img_tags.append(new_tag)
            print(f"   [+] Fetched new image: {img_url}")

    all_images_to_insert = existing_img_tags + new_img_tags
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Insert Image 1
    if all_images_to_insert:
        first_img = all_images_to_insert.pop(0)
        if '[IMAGE]' in html:
            html = html.replace('[IMAGE]', first_img)
            print("   [+] Placed Image 1 at placeholder")
        else:
            html = first_img + html
            print("   [+] Placed Image 1 at start")
            
    # Insert remaining images
    if all_images_to_insert:
        soup = BeautifulSoup(html, 'html.parser')
        paragraphs = soup.find_all('p')
        p_count = len(paragraphs)
        imgs_remaining = len(all_images_to_insert)
        
        if p_count > 0:
            for i, img_code in enumerate(all_images_to_insert):
                idx = int((i + 1) * (p_count / (imgs_remaining + 1)))
                img_soup = BeautifulSoup(img_code, 'html.parser')
                img_tag_to_insert = img_soup.find('img')
                
                if img_tag_to_insert:
                    if idx < len(paragraphs):
                        paragraphs[idx].insert_after(img_tag_to_insert)
                        print(f"   [+] Placed Image {i+2} after paragraph {idx}")
                    else:
                        soup.append(img_tag_to_insert)
        html = str(soup)

    html = html.replace("[IMAGE]", "")
    return html

# Test Case 1: Old post has 0 images. generated has placeholder.
old_html_1 = "<p>Old content</p>"
new_html_1 = "<h1>Title</h1><p>Key Takeaways</p>[IMAGE]<p>Para 1</p><p>Para 2</p><p>Para 3</p><p>Para 4</p>"
result_1 = process_images_mock(new_html_1, old_html_1, "Case 1")
print(result_1)

# Test Case 2: Old post has 1 image. generated has placeholder.
old_html_2 = "<p>Old content <img src='old1.jpg'></p>"
new_html_2 = "<h1>Title</h1><p>Key Takeaways</p>[IMAGE]<p>Para 1</p><p>Para 2</p><p>Para 3</p><p>Para 4</p>"
result_2 = process_images_mock(new_html_2, old_html_2, "Case 2")
print(result_2)

# Test Case 3: Old post has 3 images. generated has placeholder.
# Should use 1st for placeholder, distribute other 2. Fetch 0 new.
old_html_3 = "<p> <img src='old1.jpg'> <img src='old2.jpg'> <img src='old3.jpg'> </p>"
new_html_3 = "<h1>Title</h1><p>Key Takeaways</p>[IMAGE]<p>Para 1</p><p>Para 2</p><p>Para 3</p><p>Para 4</p>"
result_3 = process_images_mock(new_html_3, old_html_3, "Case 3")
print(result_3)
