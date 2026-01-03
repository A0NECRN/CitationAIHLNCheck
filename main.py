import os
import sys
import time
import glob
import argparse
from tqdm import tqdm
from src.bib_parser import parse_bibtex_file
from src.verifier import verify_citation

DEFAULT_INPUT_FILE = "input.bib"

def process_file(file_path):
    print(f"\n[*] Processing file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[-] File not found: {file_path}")
        if file_path == DEFAULT_INPUT_FILE:
            with open(DEFAULT_INPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("% Paste your BibTeX content here\n")
            print(f"[+] Created {DEFAULT_INPUT_FILE} for you.")
        return

    try:
        entries = parse_bibtex_file(file_path)
    except Exception as e:
        print(f"[!] BibTeX parsing failed: {e}")
        return

    if not entries:
        print(f"[-] No valid BibTeX entries found in {file_path}.")
        return

    print(f"[+] Found {len(entries)} entries. Verifying...")
    
    results = []
    valid_count = 0
    
    for entry in tqdm(entries, desc="Progress", unit="item"):
        verification = verify_citation(entry)
        results.append((entry, verification))
        if verification['status'] == 'valid':
            valid_count += 1
            
    report_file = f"{file_path}_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Verification Report: {os.path.basename(file_path)}\n\n")
        f.write(f"**Processed at**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for entry, result in results:
            entry_id = entry.get('ID', 'Unknown')
            title = entry.get('title', 'No Title').replace('{', '').replace('}', '')
            
            status = result['status']
            if status == 'valid':
                symbol = "✅ [PASSED]"
            elif status == 'uncertain':
                symbol = "⚠️ [DOUBTFUL]"
            elif status == 'not_found':
                symbol = "❌ [NOT FOUND]"
            else:
                symbol = "🚫 [INVALID/ERROR]"
                
            f.write(f"### {symbol} ID: {entry_id}\n")
            f.write(f"- **Original Title**: {title}\n")
            
            if status == 'valid':
                f.write(f"- **Matched Title**: {result.get('title', '')}\n")
                f.write(f"- **Similarity**: {result.get('score', 0):.2f}%\n")
                f.write(f"- **Link**: {result.get('url', '')}\n")
                f.write(f"- **Source**: {result.get('source', '')}\n")
            elif status == 'uncertain':
                f.write(f"- **Suspected Match**: {result.get('title', '')}\n")
                f.write(f"- **Similarity**: {result.get('score', 0):.2f}%\n")
                f.write(f"- **Reason**: {result.get('reason', '')}\n")
                f.write(f"- **Source**: {result.get('source', '')}\n")
            else:
                f.write(f"- **Reason**: {result.get('reason', '')}\n")
                f.write(f"- **Source**: {result.get('source', '')}\n")
            
            f.write("\n---\n\n")

        f.write(f"## Summary\n")
        f.write(f"- **Total**: {len(entries)}\n")
        f.write(f"- **Passed**: {valid_count}\n")
        f.write(f"- **Issues**: {len(entries) - valid_count}\n")

    print(f"\n[+] Verification complete! Report generated: {report_file}")
    print(f"Stats: Total {len(entries)}, Passed {valid_count}, Issues {len(entries) - valid_count}.")
    print("=" * 60 + "\n")

def main():
    print("==========================================")
    print("      CitationCheck - Verification Tool")
    print("==========================================")

    parser = argparse.ArgumentParser(description='BibTeX Citation Verifier')
    parser.add_argument('files', metavar='FILE', type=str, nargs='*',
                        help='BibTeX files to verify', default=[])
    
    args = parser.parse_args()
    
    files_to_process = args.files
    
    if not files_to_process:
        files_to_process = glob.glob("*.bib")
        
        if not files_to_process:
            files_to_process = [DEFAULT_INPUT_FILE]
            
    print(f"[*] Files to process: {files_to_process}")

    for file_path in files_to_process:
        process_file(file_path)

if __name__ == "__main__":
    main()
