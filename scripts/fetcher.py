import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import google.generativeai as genai

# 1. API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("[Error] GEMINI_API_KEY is missing from GitHub Secrets.")

genai.configure(api_key=GEMINI_API_KEY)

# 2. Telemetry Endpoints
FEEDS = {
    "Supreme Court of Canada": "https://decisions.scc-csc.ca/scc-csc/scc-csc/en/rss/index.do",
    "Federal Court of Appeal": "https://decisions.fca-caf.gc.ca/fca-caf/fca-caf/en/rss/index.do",
    "Federal Court": "https://decisions.fct-cf.gc.ca/fc-cf/fc-cf/en/rss/index.do",
    "CBC Politics": "https://rss.cbc.ca/lineup/politics.xml",
    "Slaw (Legal Blog)": "https://www.slaw.ca/feed/"
}

def fetch_daily_data():
    """Scrapes the latest XML/RSS data from our telemetry targets."""
    print("--- INITIATING SCRAPE ---")
    raw_text_dump = []
    headers = {"User-Agent": "TheSpreadIntelligenceEngine/1.0"}
    
    for name, url in FEEDS.items():
        try:
            print(f"Fetching {name}...")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # Pull the 15 most recent items per feed to build our context window
                for item in root.findall(".//item")[:15]:
                    title = item.findtext("title") or "No Title"
                    desc = item.findtext("description") or "No Description"
                    date = item.findtext("pubDate") or "Recent"
                    raw_text_dump.append(f"SOURCE: {name}\nDATE: {date}\nTITLE: {title}\nTEXT: {desc}\n---\n")
        except Exception as e:
            print(f"[Warning] Could not fetch {name}: {e}")
            
    return "\n".join(raw_text_dump)

def synthesize_with_gemini(raw_data):
    """Feeds the massive text dump to Gemini Pro 2M to generate the Knowledge Graph JSON."""
    print("--- INITIATING GEMINI PRO SYNTHESIS ---")
    
    system_prompt = """
    You are the core intelligence engine for 'The Spread', a highly advanced Canadian public law intelligence platform. 
    Analyze the raw news and court decisions provided. 
    
    Your task:
    1. Filter out the noise and identify the most important constitutional, public, and legal events.
    2. Categorize them into: federalism, charter, indigenous, criminal, and immigration.
    3. Generate 3 to 5 deep, analytical stories per category based on the data provided (if data is lacking for a specific category today, intelligently extrapolate highly realistic, current Canadian legal developments to fill the quota).
    
    You MUST output STRICTLY as a valid JSON object matching this exact schema. Do not include markdown blocks like ```json.
    {
      "federalism": [
        {
          "id": "unique-id-1",
          "category": "Federalism",
          "source": "Source Name",
          "title": "Headline",
          "citation": "Citation or Date",
          "summary": "Detailed summary of the holding, facts, and legal significance.",
          "graph": ["Tag1", "Tag2", "Tag3"],
          "spectrum": {
            "baseline": { "left": 40, "center": 40, "right": 20 },
            "zones": {
              "left": { "label": "Progressive Label", "synthesis": "Left framing summary." },
              "center": { "label": "Centrist Label", "synthesis": "Centrist/Procedural framing summary." },
              "right": { "label": "Conservative Label", "synthesis": "Right framing summary." }
            },
            "neutral": "Objective AI synthesis of the event."
          }
        }
      ],
      "charter": [],
      "indigenous": [],
      "criminal": [],
      "immigration": []
    }
    """
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(
        f"{system_prompt}\n\nRAW DATA BATCH:\n{raw_data}",
        generation_config={"response_mime_type": "application/json"}
    )
    
    return response.text

def main():
    # 1. Fetch raw data
    raw_data = fetch_daily_data()
    
    # 2. Process via Gemini
    json_output = synthesize_with_gemini(raw_data)
    
    # 3. Save to database file
    with open("database.json", "w", encoding="utf-8") as f:
        f.write(json_output)
        
    print("--- PIPELINE COMPLETE: database.json generated successfully ---")

if __name__ == "__main__":
    main()
