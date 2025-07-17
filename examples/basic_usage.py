#!/usr/bin/env python3
"""
Basic usage example for rubot as a Python library
"""

import os
from rubot.config import RubotConfig
from rubot.downloader import download_pdf
from rubot.marker import convert_pdf_to_markdown
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
    markdown_content = convert_pdf_to_markdown(pdf_path, use_cache=True, verbose=True)
    
    # Step 3: Process with LLM
    print("Processing with LLM...")
    llm_response = process_with_openrouter(
        markdown_content,
        config.default_prompt_file,
        config.default_model,
        temperature=0.1,
        max_tokens=4000,
        verbose=True
    )
    
    # Step 4: Output raw response (like CLI tool does now)
    print("\n=== RAW OPENROUTER RESPONSE ===")
    print(llm_response)
    
    # Optional: Parse for analysis (like CLI tool does in verbose mode)
    try:
        analysis = RathausUmschauAnalysis.from_llm_response(
            llm_response,
            date,
            config.default_model
        )
        
        print(f"\n=== ANALYSIS SUMMARY ===")
        print(f"- Summary length: {len(analysis.summary)} characters")
        print(f"- {len(analysis.announcements)} announcements")
        print(f"- {len(analysis.events)} events")
        print(f"- {len(analysis.important_dates)} important dates")
        
        # Save parsed analysis to file
        with open(f"rathaus_umschau_{date}_parsed.json", "w") as f:
            f.write(analysis.to_json())
        print(f"\nParsed analysis saved to rathaus_umschau_{date}_parsed.json")
        
    except Exception as e:
        print(f"\nNote: Could not parse response as structured data: {e}")
    
    # Save raw response to file (like CLI tool does)
    with open(f"rathaus_umschau_{date}_raw.json", "w") as f:
        f.write(llm_response)
    print(f"Raw response saved to rathaus_umschau_{date}_raw.json")

if __name__ == "__main__":
    main()