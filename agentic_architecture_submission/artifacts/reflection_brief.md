# Reflection & Synthesis Brief

> **Evidence status:** Generated from the local deterministic run on 2026-10-23. Test logs are under `artifacts/test_logs/`; rerun `python scripts/run_all.py` to reproduce. Context token counts are character-based estimates, not provider-tokenizer measurements.

## 1. Agentic loop and termination
- **Termination location:** `system1_agentic_loop/agent.py`, `AgentLoop.run()`. The loop continues after `stop_reason == "tool_use"`, and stops processing model turns after `stop_reason == "end_turn"`. The `for` loop also has a safety cap (`max_turns`) that escalates rather than running indefinitely.
- **Anti-pattern avoided:** blindly treating every model response as final, or allowing an unbounded tool loop.
- **Evidence:** `artifacts/agentic_run.json` contains three claims. `CLM-1001` has `tool_use → tool_use → end_turn` and routes to `standard_claims`; `CLM-1002` follows the same stop-reason sequence and escalates for risk/ambiguity; `CLM-1003` escalates because policy information is missing.
- **Test guarantee not visible in one run:** malformed or unsupported stop reasons raise `ValueError`; a happy-path trace alone cannot prove that failure handling.

## 2. Context strategy
- **Assembly location:** `system2_context_strategy/context.py`, `assemble_context()`. Structured case facts are serialized compactly; history is bounded/summarized; policy text is retained as a concise summary.
- **Preserved verbatim/structured:** identifiers, amount, description and other fields in `case_facts` remain present in the serialized facts block. **Summarized:** history is truncated to a bounded window and policy statements are joined into a compact string.
- **Evidence:** `artifacts/budget.json` reports 252 raw-baseline tokens and 95 assembled-context tokens, a 62.30% reduction using `ceil(characters/4)`. This is a reproducible character-based heuristic, not an exact Claude tokenizer count. `artifacts/context_run.json` answers 6/6 evaluation questions in the full run. In the control run without `case_facts`, amount, claim ID, and damage questions regress (3 of 6 remain answerable).
- **Trade-off:** shorter context reduces repeated historical detail but risks losing nuance. The case-facts block protects high-value fields needed for answerability.

## 3. Claude Code harness
- **Evidence:** `system3_claude_harness/CLAUDE.md` imports `@standards/api.md` and `@standards/testing.md`; `.claude/rules/python.md` and `.claude/rules/tests.md` have YAML `globs`; `.claude/commands/verify.md` defines `/verify`; `.claude/skills/inspect-readonly/SKILL.md` declares `context: fork` and only the `Read` tool.
- **Why path-scoped rules:** conventions can apply to matching files across the codebase without duplicating directory-level `CLAUDE.md` instructions in every subtree. Narrow globs reduce accidental over-application.
- **Why forked skill:** read-only inspection is isolated from the main conversation context and explicitly limited to a read tool, reducing state contamination and accidental mutation.
- **Deterministic enforcement vs prompt guidance:** the Python validator (`validate.py`) deterministically checks required files/frontmatter and exits nonzero on failure. Prose in `CLAUDE.md` and the skill body is prompt-based guidance and cannot guarantee model compliance by itself.

## 4. Layer 3 orchestration
- **SQL filtering:** `system4_orchestration/orchestrator.py`, `query_shift()` uses a parameterized SQL query to select only the requested shift and exclude closed defects. Cite `filtered_defect_count` and IDs from `artifacts/orchestration_run.json`.
- **Hot state:** `write_hot_state()` rejects payloads at or above 5 KiB. The generated run records a 100-byte hot-state file, well below the 5,120-byte limit.
- **Resume vs fresh:** `recovery_decision()` resumes a checkpoint whose age is at or below `stale_seconds` (default 3,600 seconds); it starts fresh when there is no checkpoint or the checkpoint is older than the threshold. The artifact demonstrates resume at 1,000 seconds and fresh recovery at 5,000 seconds.
- **Fork isolation:** `fork_investigation()` deep-copies state through JSON serialization and adds a separate fork scratchpad. The demo artifact should show the scratchpad in `fork_state` while `main_state_after_fork` remains unchanged.

## 5. Cross-project synthesis
- **Model layer:** `system1_agentic_loop/agent.py` (`ModelAdapter` / `AgentLoop`) represents model-turn interpretation and tool-loop control.
- **Harness layer:** `system3_claude_harness/CLAUDE.md`, `.claude/rules/`, `.claude/commands/`, and `.claude/skills/` define hierarchical instructions and scoped tooling.
- **Orchestration layer:** `system4_orchestration/orchestrator.py` manages durable state, recovery, SQL slices and isolated investigations.
- **Context management comparison:** System 2 reduces prompt payload using `budget.json`'s baseline/assembled estimates and a case-facts ablation. System 4 reduces operational state by querying only the current shift and keeping the hot-state JSON under 5 KiB while detailed records remain in SQLite. Cite measured values from both artifacts.
- **Verification:** generated logs report 30/30, 30/30, 35/35, and 33/33 passing tests (128 total), each with a system-specific log header and exit code 0. A single successful run would not prove that unsupported stop reasons are rejected, SQL parameters resist injection-like input, stale checkpoints trigger a fresh start, or missing harness metadata is detected; those are covered by tests.

## 6. Limitations and next steps
1. Replace the heuristic context token counter with the target model tokenizer before making production token-efficiency claims.
2. Add a real provider adapter only when credentials and usage/cost tracking are configured securely.
3. Validate harness configuration against the installed Claude Code version in addition to this offline structural check.
4. Add persistence durability, concurrent-run locking, schema migration and observability before production deployment.
