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
    print(f"\n[*] 正在处理文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[-] 未找到文件: {file_path}")
        if file_path == DEFAULT_INPUT_FILE:
            with open(DEFAULT_INPUT_FILE, 'w', encoding='utf-8') as f:
                f.write("% 请在此处粘贴您的 BibTeX 内容\n")
                f.write("% 示例:\n")
                f.write("% @article{vaswani2017attention,\n")
                f.write("%   title={Attention Is All You Need},\n")
                f.write("%   author={Vaswani, Ashish},\n")
                f.write("%   year={2017}\n")
                f.write("% }\n")
            print(f"[+] 已为您创建 {DEFAULT_INPUT_FILE}。")
        return

    try:
        entries = parse_bibtex_file(file_path)
    except Exception as e:
        print(f"[!] 解析 BibTeX 失败: {e}")
        return

    if not entries:
        print(f"[-] {file_path} 中没有找到有效的 BibTeX 条目。")
        return

    print(f"[+] 找到 {len(entries)} 条文献。开始查证...")
    
    results = []
    valid_count = 0
    
    for entry in tqdm(entries, desc="查证进度", unit="条"):
        verification = verify_citation(entry)
        results.append((entry, verification))
        if verification['status'] == 'valid':
            valid_count += 1
            
    # Report
    report_file = f"{file_path}_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 查证报告: {os.path.basename(file_path)}\n\n")
        f.write(f"**处理时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for entry, result in results:
            entry_id = entry.get('ID', 'Unknown')
            title = entry.get('title', 'No Title').replace('{', '').replace('}', '')
            
            status = result['status']
            if status == 'valid':
                symbol = "✅ [通过]"
            elif status == 'uncertain':
                symbol = "⚠️ [存疑]"
            elif status == 'not_found':
                symbol = "❌ [未找到]"
            else: # invalid or error
                symbol = "🚫 [无效/错误]"
                
            f.write(f"### {symbol} ID: {entry_id}\n")
            f.write(f"- **原始标题**: {title}\n")
            
            if status == 'valid':
                f.write(f"- **匹配来源**: {result.get('title', '')}\n")
                f.write(f"- **相似度**: {result.get('score', 0):.2f}%\n")
                f.write(f"- **链接**: {result.get('url', '')}\n")
                f.write(f"- **来源库**: {result.get('source', '')}\n")
            elif status == 'uncertain':
                 f.write(f"- **疑似匹配**: {result.get('title', '')}\n")
                 f.write(f"- **相似度**: {result.get('score', 0):.2f}%\n")
                 f.write(f"- **原因**: {result.get('reason', '')}\n")
                 f.write(f"- **来源库**: {result.get('source', '')}\n")
            else:
                 f.write(f"- **原因**: {result.get('reason', '')}\n")
                 f.write(f"- **来源库**: {result.get('source', '')}\n")
            
            f.write("\n---\n\n")

        f.write(f"## 统计\n")
        f.write(f"- **总计**: {len(entries)}\n")
        f.write(f"- **通过**: {valid_count}\n")
        f.write(f"- **问题**: {len(entries) - valid_count}\n")

    print(f"\n[+] 查证完成！报告已生成: {report_file}")
    print(f"文件统计: 总计 {len(entries)} 条, 通过 {valid_count} 条, 问题 {len(entries) - valid_count} 条。")
    print("=" * 60 + "\n")

def main():
    print("==========================================")
    print("      CitationCheck - 文献查证工具")
    print("==========================================")

    parser = argparse.ArgumentParser(description='BibTeX Citation Verifier')
    parser.add_argument('files', metavar='FILE', type=str, nargs='*',
                        help='BibTeX files to verify', default=[])
    
    args = parser.parse_args()
    
    files_to_process = args.files
    
    if not files_to_process:
        # No arguments provided, scan for .bib files
        files_to_process = glob.glob("*.bib")
        
        if not files_to_process:
            files_to_process = [DEFAULT_INPUT_FILE]
            
    print(f"[*] 待处理文件列表: {files_to_process}")

    for file_path in files_to_process:
        process_file(file_path)

if __name__ == "__main__":
    main()
