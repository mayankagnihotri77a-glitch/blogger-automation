from dotenv import load_dotenv
load_dotenv()
import os
import sys

# Ensure we're in the right directory for relative imports if needed, 
# though here we are in the same dir.
from email_poster import send_post_via_email

def test():
    print("--- Starting Email Post Test ---")
    user = os.getenv("EMAIL_USER")
    blogger = os.getenv("BLOGGER_EMAIL")
    print(f"Sender: {user}")
    print(f"Target: {blogger}")
    
    title = "Test Post from Antigravity Verification"
    content = "<h1>Verification Successful</h1><p>The email credentials have been correctly updated and the system is able to send posts via email.</p>"
    
    result = send_post_via_email(title, content)
    
    if result:
        print("\n>>> TEST SUCCEEDED: Email sent to Blogger.")
    else:
        print("\n>>> TEST FAILED: Email could not be sent.")

if __name__ == "__main__":
    test()
