import json
from pathlib import Path

files_to_rewrite = [
    "README.md",
    "Makefile",
    ".github/workflows/ci.yml",
    "src/pictova/demo.py",
    "tests/unit/test_demo.py",
    "tests/unit/test_file_formatting.py",
    "pyproject.toml",
    "examples/profiles/sample-publisher.yaml",
    "docs/README.md",
    "docs/ARCHITECTURE.md"
]

out = []
out.append("import os")
out.append("from pathlib import Path")
out.append("")
out.append("def rewrite_file(path, lines):")
out.append("    content = '\\n'.join(lines) + '\\n'")
out.append("    Path(path).parent.mkdir(parents=True, exist_ok=True)")
out.append("    with open(path, 'w', encoding='utf-8', newline='\\n') as f:")
out.append("        f.write(content)")
out.append("    actual = len(Path(path).read_text(encoding='utf-8').splitlines())")
out.append("    print(f'Rewrote {path}, lines: {actual}')")
out.append("    assert actual >= 20, f'File {path} is too small!'")
out.append("")

for path in files_to_rewrite:
    p = Path(path)
    if not p.exists():
        continue
    content = p.read_text(encoding='utf-8')
    lines = content.splitlines()
    var_name = path.replace("/", "_").replace(".", "_").replace("-", "_") + "_lines"
    
    out.append(f"{var_name}: list[str] = [")
    for line in lines:
        out.append(f"    {repr(line)},")
    out.append("]")
    out.append(f"rewrite_file({repr(path)}, {var_name})")
    out.append("")

Path("rewrite_files.py").write_text("\n".join(out), encoding="utf-8")
print("Generated rewrite_files.py")
