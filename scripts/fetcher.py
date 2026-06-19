import os
import json
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# Secure API Initializer using the NEW v2 Client
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("[Fatal Error] GEMINI_API_KEY is completely missing from GitHub Secrets.")

client = genai.Client(api_key=GEMINI_API_KEY)

# 21 Elite Telemetry Nodes (SCC updated to direct HTML navigation page)
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
        "https://decisions.scc-csc.ca/scc-csc/scc-csc/en/nav_date.do", # HTML Directory Front Door
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

def parse_any_date(date_str):
    if not date_str: return None
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except:
            return None

def execute_daily_triage():
    print("--- INITIATING DUAL-SPECTRUM TRIAGE EXTRACTION ---")
    raw_ingestion_batch = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}
    lookback_limit = datetime.now(timezone.utc) - timedelta(days=1)
    
    for spectrum_bracket, endpoints in FEEDS.items():
        for target_url in endpoints:
            try:
                print(f"Polling Registry: {target_url}")
                
                # SPECIAL OVERRIDE: Scraping the SCC HTML Front-Door Directly
                if "nav_date.do" in target_url:
                    response = requests.get(target_url, headers=headers, timeout=12)
                    if response.status_code != 200: continue
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    found_links = []
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if "/item/" in href and href not in [l[1] for l in found_links]:
                            if href.startswith('/'):
                                href = "https://decisions.scc-csc.ca" + href
                            title_text = a.get_text(strip=True)
                            if title_text and len(title_text) > 8:
                                found_links.append((title_text, href))
                    
                    # Force grab the top 2 latest judgments completely bypassing RSS lag
                    for title, link in found_links[:2]:
                        print(f" -> [HTML Override] Forcing Extraction of Judgment: {title}")
                        full_text_intel = clean_full_text(link)
                        raw_ingestion_batch.append({
                            "spectrum_origin": spectrum_bracket,
                            "title": title,
                            "url": link,
                            "snippet": "Direct database directory injection.",
                            "extracted_body": full_text_intel[:12000]
                        })
                    continue

                # Standard RSS/Atom Stream Engine
                response = requests.get(target_url, headers=headers, timeout=12)
                if response.status_code != 200: continue
                root = ET.fromstring(response.content)
                
                for item in root.iter():
                    clean_tag = item.tag.split('}')[-1].lower() if '}' in item.tag else item.tag.lower()
                    if clean_tag in ['item', 'entry']:
                        raw_pub_date, title, link, description = None, "Untitled Document", "", ""
                        for child in item:
                            ctag = child.tag.split('}')[-1].lower() if '}' in child.tag else child.tag.lower()
                            if ctag in ['pubdate', 'published', 'updated', 'date']: raw_pub_date = child.text
                            elif ctag == 'title': title = child.text
                            elif ctag == 'link': link = child.get('href') if child.get('href') else child.text
                            elif ctag in ['description', 'summary']: description = child.text
                                
                        parsed_date = parse_any_date(raw_pub_date)
                        if not parsed_date or parsed_date < lookback_limit: continue
                            
                        print(f" -> Processing Live Event: {title}")
                        full_text_intel = clean_full_text(link) if link else ""
                        raw_ingestion_batch.append({
                            "spectrum_origin": spectrum_bracket,
                            "title": title, "url": link, "snippet": description,
                            "extracted_body": full_text_intel[:12000]
                        })
            except Exception as error:
                print(f"[Warning] Skipping tracking node due to volatility: {error}")
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
    
    # Trigger specialized SCC analytical layout rules
    is_friday = datetime.now(timezone.utc).weekday() == 4
    scc_protocol = ""
    if is_friday:
        scc_protocol = """
    *** SPECIAL FRIDAY PROTOCOL INITIATED ***
    Today is Friday. The Supreme Court of Canada releases decisions today.
    For ANY Supreme Court of Canada (SCC) decisions you find in the data, you MUST alter your analysis to match this specialized format:
    - 'source': MUST explicitly be "Supreme Court of Canada"
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
          "citation": "June 2026 Tracking Window",
          "url": "The exact source URL provided",
          "summary": "Deep contextual distillation of the legal or policy maneuver.",
          "graph": ["Tag1", "Tag2"],
          "spectrum": {{
            "baseline": {{ "left": 33, "center": 34, "right": 33 }},
            "zones": {{
              "left": {{ "label": "Progressive Context", "synthesis": "Analysis from left/social viewpoints." }},
              "center": {{ "label": "Procedural Context", "synthesis": "Analysis from neutral/judicial viewpoints." }},
              "right": {{ "label": "Conservative Context", "synthesis": "Analysis from decentralist/market viewpoints." }}
            }},
            "neutral": "Unified objective summary statement."
          }}
        }}
      ],
      "charter": [],
      "indigenous": [],
      "criminal": [],
      "immigration": []
    }}
    """

    max_retries = 5
    for attempt in range(max_retries):
        try:
            ai_synthesis = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_instruction}\n\nDATA INPUT BATCH:\n{json.dumps(payload)}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            with open("database.json", "w", encoding="utf-8") as file:
                file.write(ai_synthesis.text)
            print("--- LIVE REBUILD METRICS APPLIED SUCCESSFULLY TO THE SPREAD ARCHIVE ---")
            break
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e):
                wait_time = 60 * (attempt + 1)
                print(f"[Warning] Google API overloaded (Attempt {attempt+1}/{max_retries}). Waiting {wait_time} seconds to try again...")
                time.sleep(wait_time)
                if attempt == max_retries - 1: raise e
            else:
                raise e

if __name__ == "__main__":
    main()
