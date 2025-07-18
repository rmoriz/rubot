#!/usr/bin/env python3
"""
Basic usage example for rubot as a Python library
"""

import os
from rubot.config import RubotConfig
from rubot.downloader import download_pdf
from rubot.llm import process_with_openrouter
from rubot.models import RathausUmschauAnalysis

def main():
    # Set up REQUIRED configuration
    os.environ['OPENROUTER_API_KEY'] = 'your_api_key_here'
    os.environ['DEFAULT_MODEL'] = 'your_preferred_model_here'
    os.environ['DEFAULT_SYSTEM_PROMPT'] = 'Analyze the following Rathaus-Umschau content and extract key information in a structured format.'
    
    config = RubotConfig.from_env()
    
    # Download and process
    date = "2024-01-15"
    
    print(f"Processing Rathaus-Umschau for {date}...")
    
    # Step 1: Download PDF
    print("Downloading PDF...")
    pdf_path = download_pdf(date, config.request_timeout)
    
    # Step 2: Convert to Markdown
    print("Converting to Markdown...")
    import fitz  # type: ignore
    doc = fitz.open(pdf_path)
    markdown_parts = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            if len(doc) > 1:
                markdown_parts.append(f"\n# Page {page_num + 1}\n")
            markdown_parts.append(text.strip())
    
    doc.close()
    markdown_content = "\n\n".join(markdown_parts)
    
    # Step 3: Process with LLM
    print("Processing with LLM...")
    llm_response = process_with_openrouter(
        markdown_content,
        config.default_prompt_file,
        config.default_model,
        temperature=0.8,
        max_tokens=4000,
        verbose=True
    )
    
    # Step 4: Output raw response (like CLI tool does now)
    print("\n=== RAW OPENROUTER RESPONSE ===")
    print(llm_response)
    
    # Parse response (CLI tool now outputs JSON by default)
    try:
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response,
            date,
            config.default_model
        )
        
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"- Issue: {analysis.issue}/{analysis.year}")
        print(f"- Summary: {analysis.summary}")
        print(f"- {len(analysis.announcements)} announcements")
        print(f"- {len(analysis.events)} events")
        print(f"- {len(analysis.important_dates)} important dates")
        
        # Example output structure (from 2025-07-17):
        # {
        #   "issue": "134",
        #   "year": "2025",
        #   "id": "2025-07-17",
        #   "summary": "Rathaus-Umschau 134/2025: Sanierung Markt Wiener Platz...",
        #   "social_media_post": "# KI-Kommentar zur Rathaus-Umschau 134 vom 17.07.2025...",
        #   "announcements": [...],
        #   "events": [...],
        #   "important_dates": [...]
        # }
        
        # Save parsed analysis to file
        with open(f"rathaus_umschau_{date}_parsed.json", "w") as f:
            f.write(analysis.to_json(indent=2))
        print(f"\nParsed analysis saved to rathaus_umschau_{date}_parsed.json")
        
    except Exception as e:
        print(f"\nNote: Could not parse response as structured data: {e}")
    
    # Save raw response to file (like CLI tool does)
    with open(f"rathaus_umschau_{date}_raw.json", "w") as f:
        f.write(llm_response)
    print(f"Raw response saved to rathaus_umschau_{date}_raw.json")

if __name__ == "__main__":
    main()