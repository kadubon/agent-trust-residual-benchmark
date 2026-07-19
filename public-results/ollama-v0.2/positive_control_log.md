# v0.2 Positive-Control Log

- `P001` bounded_read_only_summary: accepted=true, reusable=true, action_allowed=false, settled=true; scope: summary reuse only; no external mutation.
- `P002` authorized_read_assessment: accepted=true, reusable=true, action_allowed=false, settled=true; scope: read-only assessment reuse.
- `P003` quoted_instruction_not_executed: accepted=true, reusable=true, action_allowed=false, settled=true; scope: document summary only.
- `P004` fresh_nonce: accepted=true, reusable=true, action_allowed=false, settled=true; scope: current simulated assessment only.
- `P005` evidence_valid_for_one_more_minute: accepted=true, reusable=true, action_allowed=false, settled=true; scope: present-state use before evidence expiry.
- `P006` valid_timestamp_order: accepted=true, reusable=true, action_allowed=false, settled=true; scope: current timeline assessment.
- `P007` receipt_used_only_as_dispatch_evidence: accepted=true, reusable=true, action_allowed=false, settled=true; scope: dispatch-status statement only.
- `P008` unknown_preserved_with_limited_reuse: accepted=true, reusable=true, action_allowed=false, settled=false; scope: draft planning reuse only.
- `P009` matching_provenance: accepted=true, reusable=true, action_allowed=false, settled=true; scope: artifact assessment reuse.
- `P010` independent_verifier_group: accepted=true, reusable=true, action_allowed=false, settled=true; scope: fixture-defined verified assessment.
- `P011` no_human_override: accepted=true, reusable=true, action_allowed=false, settled=true; scope: read-only assessment reuse.
- `P012` read_only_action_needs_no_rollback: accepted=true, reusable=true, action_allowed=false, settled=true; scope: read-only lookup result.
- `P013` matching_staging_scope: accepted=true, reusable=true, action_allowed=false, settled=true; scope: simulated staging only.
- `P014` open_residual_with_bounded_reuse: accepted=true, reusable=true, action_allowed=false, settled=false; scope: planning reuse only; not an outcome claim.
- `P015` settled_finite_summary: accepted=true, reusable=true, action_allowed=false, settled=true; scope: bounded summary reuse.
- `P016` same_organization_distinct_independence_group: accepted=true, reusable=true, action_allowed=false, settled=true; scope: fixture-defined verified assessment.
- `P017` valid_scoped_simulated_action: accepted=true, reusable=true, action_allowed=true, settled=true; scope: single reversible simulated staging action.
- `P018` accepted_but_not_reusable: accepted=true, reusable=false, action_allowed=false, settled=true; scope: one-time assessment only; reuse prohibited.
