import glob
import re
import os
import json

def evaluate_reports():
    report_files = glob.glob("bibtests/*_report.md")
    if not report_files:
        print("No report files found in bibtests/")
        return

    # Load ground truth mapping
    try:
        with open("bibtests/ground_truth.json", "r") as f:
            truth_mapping = json.load(f)
    except FileNotFoundError:
        print("[ERROR] bibtests/ground_truth.json not found. Run generate_tests.py first.")
        return

    total_entries = 0
    true_positives = 0  # Real entries marked as PASSED
    true_negatives = 0  # Fake entries marked as NOT FOUND or DOUBTFUL
    false_positives = 0 # Fake entries marked as PASSED
    false_negatives = 0 # Real entries marked as NOT FOUND or DOUBTFUL
    
    # Detailed breakdown
    real_passed = 0
    real_doubtful = 0
    real_notfound = 0
    fake_passed = 0
    fake_doubtful = 0
    fake_notfound = 0

    print(f"Evaluating {len(report_files)} reports...")
    print("-" * 60)

    for report_path in report_files:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Pattern: ### (.*?) ID: (.*?)\n
        matches = re.findall(r"### (.*?) ID: (.*?)\n", content)
        
        for status_raw, entry_id in matches:
            total_entries += 1
            entry_id = entry_id.strip()
            
            # Determine System Verdict
            verdict = ""
            if "[PASSED]" in status_raw:
                verdict = "PASSED"
            elif "[DOUBTFUL]" in status_raw:
                verdict = "DOUBTFUL"
            elif "[NOT FOUND]" in status_raw:
                verdict = "NOT_FOUND"
            else:
                verdict = "UNKNOWN"
            
            # Look up ground truth
            if entry_id not in truth_mapping:
                print(f"[WARN] Unknown ID {entry_id}, skipping.")
                continue
                
            is_real = truth_mapping[entry_id] == "real"
            is_fake = truth_mapping[entry_id] == "fake"

            # Update Metrics
            if is_real:
                if verdict == "PASSED":
                    true_positives += 1
                    real_passed += 1
                elif verdict == "DOUBTFUL":
                    false_negatives += 1
                    real_doubtful += 1
                elif verdict == "NOT_FOUND":
                    false_negatives += 1
                    real_notfound += 1
            elif is_fake:
                if verdict == "PASSED":
                    false_positives += 1
                    fake_passed += 1
                    print(f"[FAIL] Fake entry {entry_id} was PASSED!")
                elif verdict == "DOUBTFUL":
                    true_negatives += 1
                    fake_doubtful += 1
                elif verdict == "NOT_FOUND":
                    true_negatives += 1
                    fake_notfound += 1

    accuracy = (true_positives + true_negatives) / total_entries if total_entries > 0 else 0
    
    print(f"Total Entries Evaluated: {total_entries}")
    print(f"Accuracy: {accuracy:.2%}")
    print("-" * 30)
    print("Confusion Matrix:")
    print(f"True Positives (Real -> Passed): {true_positives}")
    print(f"True Negatives (Fake -> Caught): {true_negatives}")
    print(f"False Positives (Fake -> Passed): {false_positives}")
    print(f"False Negatives (Real -> Failed): {false_negatives}")
    print("-" * 30)
    print("Detailed Breakdown:")
    print(f"Real Entries ({real_passed + real_doubtful + real_notfound}):")
    print(f"  - Passed: {real_passed}")
    print(f"  - Doubtful: {real_doubtful}")
    print(f"  - Not Found: {real_notfound}")
    print(f"Fake Entries ({fake_passed + fake_doubtful + fake_notfound}):")
    print(f"  - Passed: {fake_passed}")
    print(f"  - Doubtful: {fake_doubtful}")
    print(f"  - Not Found: {fake_notfound}")

if __name__ == "__main__":
    evaluate_reports()
