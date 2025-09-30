Format: JSON Lines (ndjson). Chaque entrée est append-only et merklisée quotidiennement.
Entry schema:
- id: "JRNL-YYYYMMDD-XXXX"
- timestamp: RFC3339
- actor: {type: "system|human", id: "..."}
- action_type: "Retrieval|Synthesis|Decision|Deploy|Map|Audit"
- input_refs: [EvidenceItem.id | Journal.id]
- output_refs: [EvidenceItem.id]
- obligations_checked: ["O-*"]
- invariants_checked: ["I-*"]
- verifiers_run: ["v_minimality","v_trace_bound",...]
- result: "pass|fail|deny"
- notes: "string"
- hash: sha256(content_without_hash)
- parent_hash: sha256(prev_entry)  // chaîne
- merkle_root_day: sha256(tree)    // ancré fin de journée
Règles:
- WORM: aucune modification; corrections via entrée 'Correction' qui réfute.
- Traçabilité: profondeur cumulée ≤ K.
- Export audit: filtre par action_type + période; bundle JSON + index.
