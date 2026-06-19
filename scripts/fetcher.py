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
    """Dynamically forks the extraction process. Jina for Paywalls, Pure HTML for Courts."""
    if is_court:
        # Court databases block Jina. We extract the raw HTML directly using a Chrome mask.
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
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
                                    "extracted_body": scc_text[:7000]
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
                                        "extracted_body": scc_text[:7000]
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
                                    "extracted_body": scc_text[:7000]
                                })
                                scc_found = True
                                break 
                                
                    continue 
                    
                # Standard Media RSS Triage Loop
                response = requests.get(target_url, headers
