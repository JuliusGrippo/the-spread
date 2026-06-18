import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import google.generativeai as genai

# API Configuration
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# The Master Feed List (Left, Center, Right, Legal)
FEEDS = {
    "Left": ["https://www.thestar.com/feed/politics/", "https://thetyee.ca/RSS/"],
    "Center": ["https://rss.cbc.ca/lineup/politics.xml", "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/politics/"],
    "Right": ["https://nationalpost.com/feed/", "https://torontosun.com/feed/"],
    "Legal": ["https://decisions.scc-csc.ca/scc-csc/scc-csc/en/rss/index.do", "https://decisions.fca-caf.gc.ca/fca-caf/fca-caf/en/rss/index.do", "https://www.slaw.ca/feed/", "https://ablawg.ca/feed/"]
}

def get_content(url):
    """Uses Jina AI reader to bypass paywalls, masquerading as Googlebot."""
    # Jina strips clutter and bypasses paywalls; setting user-agent to Googlebot
    jina_url = f"https://r.jina.ai/{url}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    try:
        response = requests.get(jina_url, headers=headers, timeout=20)
        return response.text if response.status_code == 200 else ""
    except: return ""

def fetch_daily_data():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    raw_payload = []
    
    for bias, urls in FEEDS.items():
        for url in urls:
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    pub_date = datetime.strptime(item.findtext("pubDate", "").split(",")[1].strip()[:16], "%d %b %Y").replace(tzinfo=timezone.utc)
                    if pub_date >= yesterday:
                        raw_payload.append({
                            "source": item.findtext("source", bias),
                            "title": item.findtext("title"),
                            "url": item.findtext("link"),
                            "content": get_content(item.findtext("link"))
                        })
            except: continue
    return raw_payload

def main():
    data = fetch_daily_data()
    if not data:
        with open("database.json", "w") as f: f.write("{}")
        return

    # Gemini Processing
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(
        f"Analyze these stories. Return STRICT JSON. If category empty, return []. JSON: {json.dumps(data)}",
        generation_config={"response_mime_type": "application/json"}
    )
    with open("database.json", "w") as f: f.write(response.text)

if __name__ == "__main__": main()
