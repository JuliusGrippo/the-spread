import json, requests, os, google.generativeai as genai
from datetime import datetime, timedelta, timezone

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Expanded Sources
SOURCES = [
    "https://www.thestar.com/feed/politics/", "https://thetyee.ca/RSS/",
    "https://rss.cbc.ca/lineup/politics.xml", "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/politics/",
    "https://nationalpost.com/feed/", "https://torontosun.com/feed/",
    "https://decisions.scc-csc.ca/scc-csc/scc-csc/en/rss/index.do", "https://ablawg.ca/feed/"
]

def fetch_data():
    payload = []
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    for url in SOURCES:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
            # Simplified parsing for logic...
            payload.append({"url": url, "content": "RSS Data..."}) 
        except: continue
    return payload

def main():
    data = fetch_data()
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # SYSTEM PROMPT: ENFORCING REALITY
    prompt = """Analyze the provided news. Return strict JSON. 
    1. If NO news exists for a category in the last 24h, return an empty list [].
    2. NEVER invent stories. If you cannot find real info, return empty.
    3. Max 8 stories per category. 
    4. Include the original URL for every story."""
    
    res = model.generate_content(prompt + json.dumps(data), generation_config={"response_mime_type": "application/json"})
    with open("database.json", "w") as f: f.write(res.text)

main()
