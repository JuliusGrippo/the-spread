import os
import json
import requests
import xml.etree.ElementTree as ET
import time
import re
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

# 21 Elite Telemetry Nodes
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
        "https://decisions.scc-csc.ca/scc-csc/scc-csc/en/nav_date.do",
        "https://decisions.fca-caf.gc.ca/fca-caf/fca-caf/en/rss/index.do",
        "https://decisions.fct-cf.gc.ca/fc-cf/fc-cf/en/rss/index.do",
        "https://www.slaw.ca/feed/",
        "https://ablawg.ca/feed/",
        "https://canliiconnects.org/en/commentaries.rss"
    ]
}

def clean_full_text(url, is_court=False):
    """Dynamically forks the extraction process. Jina for Paywalls, Pure HTML with Cleaner for Courts."""
    if is_court:
        # Court databases block Jina. We extract the raw HTML directly using a Chrome mask.
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                # Payload Diet: Strip hidden JS/CSS from court HTML to save massive token weight
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()
                return soup.get_text(separator=' ', strip=True)
            return ""
        except:
            return ""
    else:
        # Commercial news paywalls are bypassed via Jina using a Googlebot mask.
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
    
    chrome_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    lookback_limit = datetime.now(timezone.utc) - timedelta(days=1)
    is_friday = datetime.now(timezone.utc).weekday() == 4
    
    for spectrum_bracket, endpoints in FEEDS.items():
        for target_url in endpoints:
            try:
                print(f"Polling Registry: {target_url}")
                
                # TRIPLE-LAYER SCC FALLBACK PROTOCOL
                if "nav_date.do" in target_url:
                    if not is_friday:
                        continue 
                        
                    print(" -> [SCC Friday] Activating Triple-Layer Failsafe Protocol...")
                    scc_found = False
                    current_year = datetime.now(timezone.utc).year
                    
                    print(" -> [Level 1] Penetrating SCC Directory directly...")
                    try:
                        res_dir = requests.get(target_url, headers=chrome_headers, timeout=15)
                        dir_html = res_dir.text if res_dir.status_code == 200 else ""
                    except:
                        dir_html = ""
                    
                    if dir_html and len(dir_html) > 500:
                        # LEVEL 1: Direct Link Extraction
                        link_match = re.search(r'(?:https://decisions\.scc-csc\.ca)?(/scc-csc/scc-csc/en/item/\d+/index\.do)', dir_html)
                        if link_match:
                            scc_direct_url = "https://decisions.scc-csc.ca" + link_match.group(1)
                            print(f" -> [Level 1] Extracted direct judgment link: {scc_direct_url}")
                            scc_text = clean_full_text(scc_direct_url, is_court=True)
                            
                            if scc_text and len(scc_text) > 3000:
                                raw_ingestion_batch.append({
                                    "spectrum_origin": "Supreme Court of Canada",
                                    "title": f"Latest SCC Judgment ({current_year})",
                                    "url": scc_direct_url,
                                    "snippet": "Captured via Level 1 direct directory link.",
                                    "extracted_body": scc_text[:5000] # Trimmed for Payload Diet
                                })
                                scc_found = True
                                continue
                                
                        # LEVEL 2: CanLII Citation Extraction
                        if not scc_found:
                            print(" -> [Level 1 Failed] Activating Level 2 (CanLII Citation Extraction)...")
                            citations = re.findall(rf'({current_year}\s+SCC\s+\d+)', dir_html, re.IGNORECASE)
                            if citations:
                                latest_citation = citations[0].upper()
                                print(f" -> [Level 2] Found exact citation on directory: {latest_citation}")
                                parts = latest_citation.split()
                                canlii_url = f"https://www.canlii.org/en/ca/scc/doc/{parts[0]}/{parts[0]}scc{parts[2]}/{parts[0]}scc{parts[2]}.html".lower()
                                
                                scc_text = clean_full_text(canlii_url, is_court=True)
                                if scc_text and len(scc_text) > 3000:
                                    raw_ingestion_batch.append({
                                        "spectrum_origin": "Supreme Court of Canada",
                                        "title": f"SCC Judgment: {latest_citation}",
                                        "url": canlii_url,
                                        "snippet": "Captured via Level 2 CanLII mapping.",
                                        "extracted_body": scc_text[:5000] # Trimmed for Payload Diet
                                    })
                                    scc_found = True
                                    continue
                                    
                    # LEVEL 3: Predictive Math Fallback
                    if not scc_found:
                        print(" -> [Level 2 Failed/Locked] Activating Level 3 Predictive Citation Engine...")
                        baseline_date = datetime(2026, 6, 19, tzinfo=timezone.utc).date()
                        today = datetime.now(timezone.utc).date()
                        delta_weeks = (today - baseline_date).days // 7
                        predicted_num = 23 + delta_weeks
                        
                        for attempt_num in [predicted_num, predicted_num - 1, predicted_num - 2]:
                            if attempt_num < 1: continue
                            canlii_url = f"https://www.canlii.org/en/ca/scc/doc/{current_year}/{current_year}scc{attempt_num}/{current_year}scc{attempt_num}.html".lower()
                            print(f" -> Probing predicted URL: {canlii_url}")
                            
                            scc_text = clean_full_text(canlii_url, is_court=True)
                            
                            # Because we bypass Jina, missing CanLII pages return an empty string or short 404 page
                            if scc_text and len(scc_text) > 3000 and "404" not in scc_text and "not found" not in scc_text.lower():
                                print(f" -> [Success] Predicted capture established for {current_year} SCC {attempt_num}")
                                raw_ingestion_batch.append({
                                    "spectrum_origin": "Supreme Court of Canada",
                                    "title": f"Supreme Court Judgment: {current_year} SCC {attempt_num}",
                                    "url": canlii_url,
                                    "snippet": "Captured via Level 3 Predictive Matrix.",
                                    "extracted_body": scc_text[:5000] # Trimmed for Payload Diet
                                })
                                scc_found = True
                                break 
                                
                    continue 
                    
                # Standard Media RSS Triage Loop
                response = requests.get(target_url, headers=chrome_headers, timeout=12)
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
                        
                        # Dynamic Mask Check guarantees Jina is bypassed for all Federal Court feeds
                        is_court_link = bool(link and any(d in link.lower() for d in ['scc-csc.ca', 'fca-caf.gc.ca', 'fct-cf.gc.ca', 'canlii.org']))
                        full_text_intel = clean_full_text(link, is_court=is_court_link) if link else ""
                        
                        raw_ingestion_batch.append({
                            "spectrum_origin": spectrum_bracket,
                            "title": title, "url": link, "snippet": description,
                            "extracted_body": full_text_intel[:5000] # Payload Diet: 5000 chars instead of 12000
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
    
    is_friday = datetime.now(timezone.utc).weekday() == 4
    scc_protocol = ""
    if is_friday:
        scc_protocol = """
    *** SPECIAL FRIDAY PROTOCOL INITIATED ***
    Today is Friday. The Supreme Court of Canada releases decisions today.
    CRITICAL INSTRUCTION: You must ONLY apply this format to the entry whose 'spectrum_origin' explicitly equals "Supreme Court of Canada". Do NOT apply this format to standard news articles or Slaw commentary pieces.
    
    For verified SCC judgments ONLY:
    - 'source': MUST explicitly be "Supreme Court of Canada"
    - 'summary': Extract and summarize the lower court history (Trial & Court of Appeal) leading up to this SCC ruling.
    - 'zones.left.label': "Majority Reasons"
    - 'zones.left.synthesis': Detail the SCC Majority's reasoning and the judge split (e.g., 5-4, 7-2).
    - 'zones.center.label': "Concurring Reasons"
    - 'zones.center.synthesis': Detail any concurring opinions. If none, detail the broader policy implications.
    - 'zones.right.label': "Dissenting Reasons"
    - 'zones.right.synthesis': Detail the dissenting judges' reasons.
    - 'neutral': "Precedent Impact: [Confirming / Creating / Setting Aside] - [Brief explanation of how the common law shifts]"
    """

    system_instruction = f"""
    You are the algorithmic core of 'The Spread' Intelligence Terminal. 
    Analyze the provided collection of raw Canadian news and judicial outputs from the last 24 hours.
    {scc_protocol}
    
    Your operational rules:
    1. CRITICAL DISTRIBUTION PROTOCOL: Do NOT dump all stories into the 'federalism' category out of laziness. You must critically evaluate the dataset and distribute the stories EVENLY to their most appropriate domains: federalism, charter, indigenous, criminal, immigration. Discard irrelevant noise.
    2. Aim for up to 8 entries per category if data allows. Ensure all relevant categories receive coverage.
    3. ABSOLUTE GROUNDING: If a category contains zero real developments from the provided dataset, you MUST return an empty array [] for that key. Real news only.
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
            # The Ultimate Catch-All Failsafe for ANY network disconnect, drop, or protocol error
            wait_time = 30
            print(f"[Warning] Network transaction glitch or disconnect detected ({e}). Initiating structural recovery block (Attempt {attempt+1}/{max_retries}). Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            if attempt == max_retries - 1:
                print("[Fatal Error] Terminal could not establish a stable pipeline window with the generation clusters.")
                raise e

if __name__ == "__main__":
    main()
