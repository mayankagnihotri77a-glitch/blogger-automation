import os
import pickle
import googleapiclient.discovery
from google.auth.transport.requests import Request
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = 'token.pickle'
BLOG_ID = os.getenv("BLOGGER_BLOG_ID")

def debug():
    if not os.path.exists(TOKEN_FILE):
        print("[X] NO TOKEN FILE FOUND. Run auth.py first.")
        return

    print("--- Loading Token ---")
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)

    if not creds or not creds.valid:
        print("[X] Token is invalid or expired.")
        return

    print(f"[KEY] Granted Scopes: {creds.scopes}")
    if 'https://www.googleapis.com/auth/blogger' not in creds.scopes:
        print("[WARN] WARNING: 'https://www.googleapis.com/auth/blogger' (Write Access) is MISSING!")

    # 1. Check Identity (Who am I?)
    print("\n--- 1. Verification ---")
    try:
        # Use oauth2 v2 to get user info
        oauth_service = googleapiclient.discovery.build('oauth2', 'v2', credentials=creds)
        user_info = oauth_service.userinfo().get().execute()
        email = user_info.get('email')
        print(f"[OK] Authenticated as: {email}")
    except Exception as e:
        print(f"[X] Failed to get user email: {e}")
        print("   (This might be due to missing 'userinfo.email' scope or API disabled)")

    # 2. Check Blogger API Access (List Blogs)
    print("\n--- 2. Checking Blogger Access ---")
    try:
        service = googleapiclient.discovery.build('blogger', 'v3', credentials=creds)
        
        # List user's blogs
        blogs = service.blogs().listByUser(userId='self').execute()
        items = blogs.get('items', [])
        
        print(f"Found {len(items)} blogs for this account:")
        target_found = False
        for blog in items:
            print(f" - [{blog['id']}] {blog['name']} ({blog['url']})")
            if str(blog['id']) == str(BLOG_ID):
                target_found = True
                
        if target_found:
            print(f"[OK] Target Blog ID {BLOG_ID} found in list!")
        else:
            print(f"[X] Target Blog ID {BLOG_ID} NOT found in this account's list.")
            print("   Please check if the 'Authenticated as' email matches the Blog Admin.")

    except Exception as e:
        print(f"[X] Failed to list blogs: {e}")
        print("   (If this fails, the Blogger API might be DISABLED in Cloud Console)")

    # 3. Test Write Permission
    if target_found:
        print("\n--- 3. Testing POST Permission ---")
        try:
            body = {
                'title': 'Debug Access Test',
                'content': '<p>This is a test post to verify API permissions.</p>',
                'labels': ['Debug']
            }
            # Try Draft first
            res = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=True).execute()
            print(f"[OK] SUCCESS! Created Draft Post: {res.get('url')}")
            print("   (Permissions are working!)")
            
            # Cleanup (Delete the test post)
            try:
                post_id = res['id']
                service.posts().delete(blogId=BLOG_ID, postId=post_id).execute()
                print("   (Cleaned up: Test post deleted)")
            except:
                pass
                
        except Exception as e:
            print(f"[X] POST FAILED: {e}")
            if "403" in str(e):
                print("   -> 403 Forbidden: The API works, but you don't have WRITE permission to this specific blog.")
            if "blocked" in str(e).lower():
                print("   -> API Blocked: Check Cloud Console for Billing/Quota issues.")

    input("\nPress Enter to close details...")

if __name__ == "__main__":
    debug()
