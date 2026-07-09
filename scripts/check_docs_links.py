#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

def check_links_in_file(file_path: Path):
    if not file_path.exists():
        print(f"Error: {file_path} does not exist.")
        return 1

    content = file_path.read_text(encoding="utf-8")
    parent_dir = file_path.parent
    broken_links = []

    # Match markdown links: [text](target)
    # Exclude image links if they start with ! but we can just use a regex
    # Actually, a simple regex: \[[^\]]*\]\(([^)]+)\)
    link_pattern = re.compile(r'\[[^\]]*\]\(([^)]+)\)')

    for match in link_pattern.finditer(content):
        target = match.group(1)
        # Skip http/https links, mailto, etc.
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        
        # Strip anchors
        path_part = target.split("#")[0]
        if not path_part:
            continue
            
        target_path = (parent_dir / path_part).resolve()
        if not target_path.exists():
            broken_links.append(f"  Broken link: {target} -> {target_path}")

    if broken_links:
        print(f"Broken links found in {file_path}:")
        for link in broken_links:
            print(link)
        return 1
    
    return 0

def main():
    repo_root = Path(__file__).resolve().parent.parent
    files_to_check = [
        repo_root / "README.md",
        repo_root / "docs" / "README.md"
    ]
    
    exit_code = 0
    for f in files_to_check:
        if check_links_in_file(f) != 0:
            exit_code = 1
            
    if exit_code == 0:
        print("All local documentation links are valid.")
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
