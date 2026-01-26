import os
import sys
import time
import glob
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.bib_parser import parse_bibtex_file
from src.verifier import verify_citation

DEFAULT_INPUT_FILE = "input.bib"
MAX_WORKERS = 5

def process_file(file_path):
    print(f"\n[*] Processing file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[-] File not found: {file_path}")
        return

    try:
        entries = parse_bibtex_file(file_path)
    except Exception as e:
        print(f"[!] BibTeX parsing failed: {e}")
        return

    if not entries:
        print(f"[-] No valid BibTeX entries found in {file_path}.")
        return

    print(f"[+] Found {len(entries)} entries. Verifying in parallel...")
    
    results = []
    valid_count = 0
    uncertain_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_entry = {executor.submit(verify_citation, entry): entry for entry in entries}
        
        for future in tqdm(as_completed(future_to_entry), total=len(entries), desc="Verifying", unit="entry"):
            entry = future_to_entry[future]
            try:
                verification = future.result()
                results.append((entry, verification))
                status = verification['status']
                if status == 'valid':
                    valid_count += 1
                elif status == 'uncertain':
                    uncertain_count += 1
                else:
                    failed_count += 1
            except Exception as exc:
                print(f"[!] Error verifying entry {entry.get('ID', 'unknown')}: {exc}")
                failed_count += 1
    
    # Generate Report
    report_file = f"{file_path}_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Verification Report: {os.path.basename(file_path)}\n\n")
        f.write(f"**Processed at**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Detailed Results\n\n")
        for entry, result in results:
            entry_id = entry.get('ID', 'Unknown')
            title = entry.get('title', 'No Title').replace('{', '').replace('}', '')
            status = result['status']
            
            if status == 'valid':
                symbol = "✅ [PASSED]"
            elif status == 'uncertain':
                symbol = "⚠️ [DOUBTFUL]"
            else:
                symbol = "❌ [NOT FOUND]"
                
            f.write(f"### {symbol} ID: {entry_id}\n")
            f.write(f"- **Original Title**: {title}\n")
            
            if status == 'valid':
                f.write(f"- **Matched Title**: {result.get('title', '')}\n")
                f.write(f"- **Similarity**: {result.get('score', 0):.2f}%\n")
                f.write(f"- **Link**: {result.get('url', '')}\n")
                f.write(f"- **Source**: {result.get('source', '')}\n")
            elif status == 'uncertain':
                f.write(f"- **Reason**: {result.get('reason', '')}\n")
                f.write(f"- **Source**: {result.get('source', '')}\n")
            else:
                f.write(f"- **Reason**: {result.get('reason', 'No match found above threshold')}\n")
            
            f.write("\n---\n\n")

        f.write(f"## Summary\n")
        f.write(f"- **Total**: {len(entries)}\n")
        f.write(f"- **Passed**: {valid_count}\n")
        f.write(f"- **Doubtful**: {uncertain_count}\n")
        f.write(f"- **Not Found**: {failed_count}\n")

    # Console Summary
    print(f"\n{'-'*30}")
    print(f"   VERIFICATION SUMMARY")
    print(f"{'-'*30}")
    print(f" Total Entries: {len(entries)}")
    print(f" [✅] Passed:    {valid_count}")
    print(f" [⚠️] Doubtful:  {uncertain_count}")
    print(f" [❌] Not Found: {failed_count}")
    print(f" {'-'*30}")
    print(f" Report generated: {report_file}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Citation Accuracy Checker")
    parser.add_argument("input", nargs="?", help="Input .bib file (default: scan current dir)")
    args = parser.parse_args()

    if args.input:
        process_file(args.input)
    else:
        bib_files = glob.glob("*.bib")
        if not bib_files:
            print("[-] No .bib files found in current directory.")
            # Create default if empty
            with open(DEFAULT_INPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("% Paste your BibTeX content here\n")
            print(f"[+] Created {DEFAULT_INPUT_FILE} for you.")
        else:
            for bib_file in bib_files:
                process_file(bib_file)
