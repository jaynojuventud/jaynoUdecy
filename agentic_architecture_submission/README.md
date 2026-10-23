# Agentic Systems Architecture — Complete Submission

Four offline-first Python reference systems for agent loops, context budgeting, Claude Code harness configuration, and stateful orchestration. The examples use deterministic local fixtures so they can be tested without paid model access or external credentials.

## Requirements
- Python 3.10+
- `pytest` (install with `python -m pip install pytest`)

## Run
From this directory:
```bash
python -m pip install pytest
python scripts/run_all.py
```
The runner executes the four project test suites independently, writes identifiable logs under `artifacts/test_logs/`, and regenerates run artifacts. Expected suite counts are 30 + 30 + 35 + 33 = 128. Test output in this package is not pre-claimed: run the command locally to create the authoritative logs.

Run an individual system:
```bash
python -m pytest system1_agentic_loop/tests -q
python -m pytest system2_context_strategy/tests -q
python -m pytest system3_claude_harness/tests -q
python -m pytest system4_orchestration/tests -q
```

## Systems
1. `system1_agentic_loop`: stop-reason-driven tool loop and claim routing/escalation.
2. `system2_context_strategy`: context assembly, token budget estimate, evaluation and ablation.
3. `system3_claude_harness`: modular Claude Code configuration and static validator.
4. `system4_orchestration`: hot/cold state, SQL-filtered shift slice, checkpoint recovery, isolated forks.

## Evidence and limits
- `scripts/run_all.py` creates run outputs and test logs from actual local execution.
- The context token counter is a reproducible heuristic (roughly one token per four characters), not a tokenizer's exact count. Replace it with the target model tokenizer for production measurements.
- The model interface in System 1 is a deterministic fake adapter. To use a real provider, implement `ModelAdapter` and configure credentials securely outside the repository.
- Claude Code config validation is a local structural validator; it does not invoke Claude Code or guarantee compatibility with every future Claude Code release.
- `artifacts/reflection_brief.md` is a template/report scaffold with clearly labeled values to fill from the run-generated artifacts. Do not submit unverified values as personal measurements.
