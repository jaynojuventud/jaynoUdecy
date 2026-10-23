"""Structural validator for the repository's Claude Code harness configuration."""
from pathlib import Path
import re, json
ROOT=Path(__file__).resolve().parent

def validate(root=ROOT):
    root=Path(root); errors=[]; checks=[]
    main=root/'CLAUDE.md'
    if not main.exists(): errors.append('missing CLAUDE.md')
    else:
        txt=main.read_text(); imports=re.findall(r'^@([^\s]+)',txt,re.M)
        if not imports: errors.append('CLAUDE.md must import modular standards using @path references')
        for imp in imports:
            if not (root/imp).exists(): errors.append(f'missing imported file: {imp}')
        checks.append('modular imports')
    rules=list((root/'.claude/rules').glob('*.md'))
    if not rules: errors.append('no path-scoped rules')
    for f in rules:
        txt=f.read_text()
        if not txt.startswith('---') or not re.search(r'(?m)^globs:\s*.+',txt): errors.append(f'{f.name}: YAML frontmatter must declare globs')
    checks.append('path-scoped rules')
    commands=list((root/'.claude/commands').glob('*.md'))
    if not commands: errors.append('no project slash command')
    checks.append('slash command')
    skills=list((root/'.claude/skills').glob('*/SKILL.md'))
    if not skills: errors.append('no skill')
    for f in skills:
        txt=f.read_text()
        if not re.search(r'(?m)^context:\s*fork\s*$',txt): errors.append(f'{f}: skill must use context: fork')
        if not re.search(r'(?m)^allowed-tools:\s*\n(?:\s+-\s*Read\s*\n?)+',txt): errors.append(f'{f}: allowed-tools must be read-only')
    checks.append('forked read-only skill')
    return {"ok":not errors,"checks":checks,"errors":errors}
if __name__=='__main__':
    result=validate(); print(json.dumps(result,indent=2)); raise SystemExit(0 if result['ok'] else 1)
