GENERATOR_SYSTEM = (
    "You are a code patch generator. Output ONLY valid JSON per the schema. "
    "Be concise, safe, and prefer minimal diffs that improve compliance."
)
GENERATOR_USER_TMPL = """Task: {task}
ContextSummary: {context}
Obligations (K): {obligations}
Return JSON with EXACT keys:
- patch_unified: string        # unified diff to apply
- rationale: string            # why this satisfies K
- predicted_obligations_satisfied: string[]  # subset of K you satisfy
- risk_score: number           # 0..1
- notes: string
Constraints:
- No external network.
- Keep changes minimal and reversible.
- If unsure, prefer a conservative patch that increases compliance without breaking tests."""
