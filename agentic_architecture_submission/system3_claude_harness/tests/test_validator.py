import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from validate import validate, ROOT
@pytest.mark.parametrize('i',range(10))
def test_valid_config_repeats(i): assert validate()['ok'] is True
@pytest.mark.parametrize('file', ['CLAUDE.md','standards/api.md','standards/testing.md','.claude/rules/python.md','.claude/rules/tests.md','.claude/commands/verify.md','.claude/skills/inspect-readonly/SKILL.md'])
def test_required_files_exist(file): assert (ROOT/file).is_file()
@pytest.mark.parametrize('i',range(6))
def test_imports_resolve(i):
 r=validate(); assert 'modular imports' in r['checks'] and not any('missing imported' in e for e in r['errors'])
@pytest.mark.parametrize('i',range(6))
def test_rule_files_have_globs(i):
 for p in (ROOT/'.claude/rules').glob('*.md'): assert 'globs:' in p.read_text().split('---',2)[1]
@pytest.mark.parametrize('i',range(5))
def test_skill_is_forked_and_read_only(i):
 t=(ROOT/'.claude/skills/inspect-readonly/SKILL.md').read_text(); assert 'context: fork' in t and '- Read' in t and '- Bash' not in t
@pytest.mark.parametrize('i',range(1))
def test_validator_contract(i): assert set(validate())=={'ok','checks','errors'}
