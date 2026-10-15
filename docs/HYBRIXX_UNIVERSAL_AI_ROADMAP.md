# HYBRIXX Universal Intelligence — architecture roadmap

Status: DESIGN PROPOSAL. Not a claim of general intelligence or autonomous learning.

## Mission
Expand the existing paper-only trading research system into a general-purpose AI assistant capable of conversation, research, coding, planning, structured memory, and controlled tool use. Preserve all existing paper-only and fail-closed security gates.

## Separation of concerns
1. Language model adapter: pluggable local or hosted model, explicit configuration and no credentials in git.
2. Task orchestrator: plan, delegate, evaluate, and stop; no hidden execution.
3. Tool registry: typed allowlisted tools with least-privilege scopes; read-only by default; human approval for mutations.
4. Memory: source-attributed knowledge records with timestamps, privacy controls, deletion, and provenance; no secrets in reports.
5. Learning lab: collect feedback and benchmark outcomes; propose prompt/rule/model changes in a sandbox; promote only after regression tests and human approval. Never train automatically on untrusted tool outputs.
6. Verification: independent factuality, code tests, dataset leakage detection, and out-of-sample evaluation.
7. Trading domain: existing HYBRIXX modules remain isolated; no real-money authorization, keys, transfers, or order permissions.
8. Governance: policy enforcement, audit trail, budgets, rate limits, emergency stop and rollback.
9. Interface: one dashboard with separate evidence, confidence, approval and operational-status panels.

## First milestone: safe MVP
- Define task and tool schemas.
- Add offline memory store with deterministic tests and provenance.
- Implement a read-only planning interface with a mock model for CI.
- Connect existing unified_intelligence_report.json as one read-only domain source.
- Measure task accuracy, citation validity, tool permissions, cost and regression rates.
- Require explicit approval before external writes, emails, code deployment or financial actions.

## Non-goals
- No assertion of sentience, AGI, guaranteed financial returns or unsupervised self-modification.
- No changes to multi_state.json or existing buy gates.
- No unrestricted network, shell, account transfers, credentials or broker access.

## Acceptance criteria
- Every executed tool call logged with actor, permission, result and timestamp.
- Missing permissions fail closed.
- Untrusted retrieved content cannot become system instructions.
- Memory items retain source and can be corrected/deleted.
- Learning candidates never auto-promote.
- Paper-trading gates remain unaffected by the universal assistant.
