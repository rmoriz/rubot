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
    os.environ['DEFAULT_MODEL'] = 'anthropic/claude-3-haiku'
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
    markdown_content = convert_pdf_to_markdown(pdf_path)
    
    # Step 3: Process with LLM
    print("Processing with LLM...")
    llm_response = process_with_openrouter(
        markdown_content,
        config.default_prompt_file,
        config.default_model
    )
    
    # Step 4: Parse result
    analysis = RathausUmschauAnalysis.from_llm_response(
        llm_response,
        date,
        config.default_model
    )
    
    # Output results
    print(f"\nAnalysis Summary:")
    print(f"- {len(analysis.announcements)} announcements")
    print(f"- {len(analysis.events)} events")
    print(f"- {len(analysis.important_dates)} important dates")
    
    # Save to file
    with open(f"rathaus_umschau_{date}.json", "w") as f:
        f.write(analysis.to_json())
    
    print(f"\nResults saved to rathaus_umschau_{date}.json")

if __name__ == "__main__":
    main()