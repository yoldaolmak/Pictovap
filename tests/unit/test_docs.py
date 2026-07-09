import re
from pathlib import Path

def test_all_markdown_links():
    repo_root = Path(__file__).resolve().parent.parent.parent
    
    files_to_check = [
        repo_root / "README.md",
        repo_root / "docs" / "README.md",
        repo_root / "docs" / "release-checklist.md",
        repo_root / "docs" / "adoption-playbook.md",
        repo_root / "docs" / "release-notes" / "v0.2.0.md",
        repo_root / "docs" / "contributing" / "starter-issues.md",
    ]
    
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    broken = []
    
    for file_path in files_to_check:
        if not file_path.exists():
            continue
            
        content = file_path.read_text(encoding="utf-8")
        base_dir = file_path.parent
        
        for match in link_pattern.finditer(content):
            link_target = match.group(2)
            
            # Skip external links and internal fragment anchors
            if link_target.startswith("http") or link_target.startswith("#"):
                continue
                
            path_part = link_target.split("#")[0]
            if not path_part:
                continue
                
            resolved = (base_dir / path_part).resolve()
            if not resolved.exists():
                broken.append(f"Broken link in {file_path.name}: {link_target} -> {resolved}")
                
    assert not broken, "\n".join(broken)
