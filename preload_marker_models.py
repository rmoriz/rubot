#!/usr/bin/env python3
"""
Script to pre-download marker-pdf models during Docker build
"""

import os
import sys
import tempfile
from pathlib import Path
import subprocess

# Set environment variables for cache and marker
os.environ['CACHE_ROOT'] = '/tmp/cache'
os.environ['HF_HOME'] = '/tmp/cache/huggingface'
os.environ['XDG_CACHE_HOME'] = '/tmp/cache'
os.environ['MARKER_FONT_DIR'] = '/tmp/cache/marker_fonts'

# Create a minimal PDF content (just enough to trigger model downloads)
pdf_content = b'''%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000059 00000 n 
0000000118 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
298
%%EOF'''

def main():
    print("Pre-downloading marker-pdf models...")
    
    # Create cache directories
    Path("/tmp/cache").mkdir(parents=True, exist_ok=True)
    Path("/tmp/cache/huggingface").mkdir(parents=True, exist_ok=True)
    Path("/tmp/cache/marker").mkdir(parents=True, exist_ok=True)
    Path("/tmp/cache/marker_fonts").mkdir(parents=True, exist_ok=True)
    
    # Ensure marker's static directory exists and is writable
    static_dir = Path.home() / ".local/lib/python3.13/site-packages/static"
    static_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created static directory at: {static_dir}")
    
    # Write minimal PDF to trigger model downloads
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False, dir='/tmp/cache') as f:
        f.write(pdf_content)
        pdf_path = f.name
    
    try:
        print(f"Created test PDF at: {pdf_path}")
        
        # Run marker to trigger model downloads
        result = subprocess.run([
            'marker_single', 
            pdf_path, 
            '--output_dir', '/tmp/cache/test_model_download'
        ], capture_output=True, text=True, timeout=300, check=False)
        
        print("Marker command executed")
        if result.stdout:
            print("STDOUT:", result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
        
    except Exception as e:
        print(f"Expected error during model download: {e}")
    finally:
        # Clean up
        Path(pdf_path).unlink(missing_ok=True)
        
    # Check if models were downloaded
    model_files = list(Path("/tmp/cache").rglob("*.bin"))
    json_files = list(Path("/tmp/cache").rglob("*.json"))
    
    print(f"Found {len(model_files)} .bin files and {len(json_files)} .json files")
    for f in model_files[:3]:
        print(f"  Model: {f.name} ({f.stat().st_size} bytes)")
    
    print("Model pre-download completed successfully!")

if __name__ == "__main__":
    main()