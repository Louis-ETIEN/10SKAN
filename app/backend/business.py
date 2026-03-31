from bs4 import BeautifulSoup
import re

ITEM_1_RE = re.compile(r'item\s*1[^a-zA-Z]{0,10}business', re.IGNORECASE)
ITEM_1a_RE = re.compile(r'item\s*1a[^a-zA-Z]{0,10}risk', re.IGNORECASE)

def html_to_text(html): 
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    lines = [line.strip() for line in text.splitlines()]
    
    text = "".join([line for line in lines if line])

    return text



