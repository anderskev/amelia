import os
import glob
import re

commands_dir = ".gemini/commands"
md_files = glob.glob(os.path.join(commands_dir, "*.md"))

for md_file in md_files:
    with open(md_file, "r") as f:
        content = f.read()

    desc_match = re.search(r'^description:\s*(.+)$', content, re.MULTILINE)
    
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        description = os.path.basename(md_file).replace('.md', '')

    toml_path = md_file.replace(".md", ".toml")
    safe_content = content.replace('"""', '\"\"\"')
    
    with open(toml_path, "w") as f:
        f.write(f'description = "{description}"\n')
        f.write('\n')
        f.write('prompt = """\n')
        f.write(safe_content)
        f.write('\n"""\n')
    
    os.remove(md_file)
    print(f"Converted {md_file} to {toml_path}")