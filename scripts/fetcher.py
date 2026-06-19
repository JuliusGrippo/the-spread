import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from google import genai
from google.genai import types

# Secure API Initializer using the NEW v2 Client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("[Fatal Error] GEMINI_API_KEY is completely missing from GitHub Secrets.")

client = genai.Client(api_key=GEMINI_API_KEY)

# 21 Elite Telemetry Nodes (Left, Center, Right, and Courts/Commentary)
FEEDS = {
    "Left": [
        "https://www.thestar.com/feed/politics/",
        "https://thetyee.ca/RSS/",
        "https://pressprogress.ca/feed/",
        "https://rabble.ca/feed/",
        "https://thenarwhal.ca/feed/"
    ],
    "Center": [
        "https://rss.cbc.ca/lineup/politics.xml",
        "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/politics/",
        "https://globalnews.ca/politics/feed/",
        "https://www.ctvnews.ca/rss/politics/1.822391",
        "https://policyoptions.irpp.org/feed/"
    ],
    "Right": [
        "https://nationalpost.com/feed/",
        "https://torontosun.com/feed/",
        "https://thehub.ca/feed/",
        "https://tnc.news/feed/",
        "https://www.westernstandard.news/search/?f=rss&t=article&l=15&c=news"
    ],
    "Legal & Courts": [
        "https://decisions.scc-csc.ca/scc-csc/scc-csc/en/rss/index.do",
        "https://decisions.fca-caf.gc.ca/fca-caf/fca-caf/en/rss/index.do",
        "https://decisions.fct-cf.gc.ca/fc-cf/fc-cf/en/rss/index.do",
        "https://www.slaw.ca/feed/",
        "https://ablawg.ca/feed/",
        "https://canliiconnects.org/en/commentaries.rss"
    ]
}

def clean_full_text(url):
    """Pings the Jina extraction layer using a verified Googlebot signature to unwrap paywalls."""
    jina_endpoint = f"https://r.jina.ai/{url}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    try:
        res = requests.get(jina_endpoint, headers=headers, timeout=15)
        return res.text if res.status_code == 200 else ""
    except:
        return ""

def execute_daily_triage():
    print("--- INITIATING DUAL-SPECTRUM TRIAGE EXTRACTION ---")
    raw_ingestion_batch = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    lookback_limit = datetime.now(timezone.utc) - timedelta(days=1)
    
    for spectrum_bracket, endpoints in FEEDS.items():
        for target_url in endpoints:
            try:
                print(f"Polling Registry: {target_url}")
                response = requests.get(target_url, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue
                    
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    raw_pub_date = item.findtext("pubDate")
                    if not raw_pub_date:
                        continue
                        
                    parsed_date = parsedate_to_datetime(raw_pub_date)
                    if parsed_date < lookback_limit:
                        continue # Enforces the strict 24-hour cutoff horizon
                        
                    title = item.findtext("title") or "Untitled Document"
                    link = item.findtext("link") or ""
                    description = item.findtext("description") or ""
                    
                    print(f" -> Processing Live Event: {title}")
                    full_text_intel = clean_full_text(link) if link else ""
                    
                    raw_ingestion_batch.append({
                        "spectrum_origin": spectrum_bracket,
                        "title": title,
                        "url": link,
                        "snippet": description,
                        "extracted_body": full_text_intel[:12000] # Safe ceiling for token payload density
                    })
            except Exception as error:
                print(f"[Warning] Skipping tracking node due to runtime volatility: {error}")
                continue
                
    return raw_ingestion_batch

def main():
    payload = execute_daily_triage()
    if not payload:
        print("Zero matching telemetry units discovered in the past 24 hours.")
        with open("database.json", "w", encoding="utf-8") as f:
            f.write(json.dumps({"federalism":[], "charter":[], "indigenous":[], "criminal":[], "immigration":[]}))
        return

    print(f"--- FEED TRIAGE COMPLETE: {len(payload)} RECENT ENTRIES SENT TO GEMINI ---")
    
    # Check if today is Friday to trigger SCC Protocol
    is_friday = datetime.now(timezone.utc).weekday() == 4
    
    scc_protocol = ""
    if is_friday:
        scc_protocol = """
    *** SPECIAL FRIDAY PROTOCOL INITIATED ***
    Today is Friday. The Supreme Court of Canada releases decisions today.
    For ANY Supreme Court of Canada (SCC) decisions you find in the data, you MUST alter your analysis to match this specialized format:
    - 'summary': You must extract and summarize the lower court decisions (Trial & Court of Appeal) leading up to the SCC ruling.
    - 'zones.left.label': "Majority Reasons"
    - 'zones.left.synthesis': Detail the SCC Majority's reasoning and the judge split (e.g., 5-4, 7-2).
    - 'zones.center.label': "Concurring Reasons"
    - 'zones.center.synthesis': Detail any concurring opinions. If none, detail the broader policy implications.
    - 'zones.right.label': "Dissenting Reasons"
    - 'zones.right.synthesis': Detail the dissenting judges' reasons.
    - 'neutral': "Precedent Impact: [Confirming / Creating / Setting Aside] - [Brief explanation of how the common law or constitutional doctrine shifts]"
    """

    system_instruction = f"""
    You are the algorithmic core of 'The Spread' Intelligence Terminal. 
    Analyze the provided collection of raw Canadian news and judicial outputs from the last 24 hours.
    {scc_protocol}
    Your operational rules:
    1. Filter the events and compile entries for these specific domains: federalism, charter, indigenous, criminal, immigration.
    2. Aim for up to 8 entries per category if data allows.
    3. ABSOLUTE GROUNDING: If a category contains zero real developments from the provided dataset, you MUST return an empty array [] for that key. Do not extrapolate, simulate, or invent historical analogies. Real news only.
    4. For every entry, generate a complete architectural analysis including a multi-angle spectrum map (left, center, right), an objective summary, and metadata.
    5. Always preserve the exact item URL in the 'url' field.
    
    Output format: You must return a single, clean JSON object matching this schema without markdown formatting blocks.
    {{
      "federalism": [
        {{
          "id": "unique-hash",
          "category": "Federalism",
          "source": "Outlet Name",
          "title": "Clear Technical Summary Headline",
          "citation": "June 2026
