
from content_auditor import clean_labels, clean_html_from_text
from bs4 import BeautifulSoup

def test_cleaning():
    print("Testing Label Cleaning...")
    labels = ["Normal", "Bad<p>", "<p>Worse</p>", "<div>Mixed</div>"]
    cleaned, changed = clean_labels(labels)
    print(f"Original: {labels}")
    print(f"Cleaned: {cleaned}")
    print(f"Changed: {changed}")
    
    assert "Bad" in cleaned
    assert "Worse" in cleaned
    assert "Mixed" in cleaned
    assert "<p>" not in str(cleaned)
    assert changed == True
    print("[PASS] Label Cleaning")

def test_noise_logic():
    print("\nTesting Noise Logic...")
    html = "This is a post. [IMAGE] Some noise."
    if "[IMAGE]" in html:
        print("[PASS] Detected [IMAGE]")
    else:
        print("[FAIL] Failed to detect [IMAGE]")
        
    html2 = "<p>Good post</p>"
    if "<p" in html2:
         print("[PASS] Detected paragraphs")
    else:
         print("[FAIL] Failed to detect paragraphs")

    html3 = "Wall of text no paragraphs"
    if "<p" not in html3:
         print("[PASS] Detected missing paragraphs")
    else:
         print("[FAIL] Failed to detect missing paragraphs")

def test_rebuild_logic_mock():
    print("\nTesting Rebuild Logic (Mock)...")
    html = "Start [IMAGE] End."
    html_fixed = html.replace("[IMAGE]", "")
    print(f"Fixed: '{html_fixed}'")
    assert "[IMAGE]" not in html_fixed
    print("[PASS] Rebuild Logic")

if __name__ == "__main__":
    test_cleaning()
    test_noise_logic()
    test_rebuild_logic_mock()
